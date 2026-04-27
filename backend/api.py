from __future__ import annotations

import asyncio
import sys
import os

# Ensure repo root is on sys.path when running as `uvicorn backend.api:app`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path

import logging

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.analysis_jobs import AnalysisJobStore
from backend.models import AutoScanConfig, PortStatus, RiskLevel
from backend.port_registry import PortRegistry
from backend.route_registry import RouteRegistry
from backend.route_scanner import RouteRiskScanner
from backend.scanner import PortRiskScanner
from backend.scheduler import AutoScanScheduler
from backend.geo_utils import find_affected_cities, find_affected_routes
from backend.route_geometry import get_geometry
from backend.risk_rules import apply_port_rules, apply_route_rules, apply_route_propagation
from backend.port_news_analyst import PortNewsAnalyst
from backend.simulation import EventType, SimulationStore
from backend.websocket_manager import ConnectionManager
from src.core.event_bus import EventBus
from src.core.mcp_loader import MCPServerConnection
from src.tools.inventory_db import init_db

_logger = logging.getLogger(__name__)


# ── singletons ────────────────────────────────────────────────────────────────

registry = PortRegistry()
route_registry = RouteRegistry()
ws_manager = ConnectionManager()
scanner = PortRiskScanner()
route_scanner = RouteRiskScanner()
job_store = AnalysisJobStore()
simulations = SimulationStore()
auto_scan_config = AutoScanConfig()
port_news_analyst = PortNewsAnalyst(ws_manager)


async def _scan_all() -> None:
    """Scan every monitored port and broadcast results."""
    for port_status in registry.list_ports():
        await _scan_single(port_status.city)


scheduler = AutoScanScheduler(scan_all_fn=_scan_all)


_MCP_SERVERS = {
    "weather":   "mcp_servers/weather_server.py",
    "news":      "mcp_servers/news_server.py",
    "inventory": "mcp_servers/inventory_server.py",
    "routing":   "mcp_servers/routing_server.py",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # EventBus — graceful no-op if NATS unreachable
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    event_bus = EventBus(url=nats_url)
    job_store._event_bus = event_bus

    # MCP servers — fall back to direct-Python tools on failure
    _mcp_conns: list[MCPServerConnection] = []
    try:
        conns = {name: MCPServerConnection(script) for name, script in _MCP_SERVERS.items()}
        _mcp_conns = list(conns.values())
        job_store._mcp_tools = {name: conn.to_tools() for name, conn in conns.items()}
        _logger.info("[API] MCP servers ready.")
    except Exception as exc:
        _logger.warning("[API] MCP startup failed (%s) — using direct-Python tools.", exc)
        job_store._mcp_tools = None

    yield

    for conn in _mcp_conns:
        try:
            conn.close()
        except Exception:
            pass
    try:
        event_bus.close()
    except Exception:
        pass
    await scheduler.stop()


# ── app ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Supply Chain Risk API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── request bodies ────────────────────────────────────────────────────────────

class AddPortBody(BaseModel):
    city: str


class AutoScanBody(BaseModel):
    enabled: bool
    interval_minutes: int = 15


class AddRouteBody(BaseModel):
    origin: str
    destination: str
    route_type: str = "maritime"   # maritime | terrestrial | air


class CreateSimulationBody(BaseModel):
    event_type: EventType
    affected_cities: list[str]
    description: str | None = None
    severity: RiskLevel | None = None
    polygon: list[list[float]] | None = None


class CreateCoordSimulationBody(BaseModel):
    lat: float
    lon: float
    radius_km: float = 300.0
    event_type: EventType
    description: str | None = None
    severity: RiskLevel | None = None


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/api/ports")
async def list_ports() -> list[dict]:
    return [s.model_dump(mode="json") for s in registry.list_ports()]


@app.post("/api/ports", status_code=201)
async def add_port(body: AddPortBody) -> dict:
    city = body.city.strip()
    if not city:
        raise HTTPException(400, "city must not be empty")
    added = registry.add_port(city)
    if not added:
        raise HTTPException(409, f"Port '{city}' already monitored")
    await ws_manager.broadcast("port.added", {"city": city})
    # Kick off a background scan for the newly added port
    asyncio.create_task(_scan_single(city))
    return {"city": city}


@app.delete("/api/ports/{city}")
async def remove_port(city: str) -> dict:
    removed = registry.remove_port(city)
    if not removed:
        raise HTTPException(404, f"Port '{city}' not found")
    await ws_manager.broadcast("port.removed", {"city": city})
    return {"city": city}


@app.post("/api/scan")
async def scan_all_now() -> dict:
    asyncio.create_task(_scan_all())
    return {"message": "Scan started for all ports"}


@app.post("/api/scan/{city}")
async def scan_port_now(city: str) -> dict:
    if not registry.has_port(city):
        raise HTTPException(404, f"Port '{city}' not monitored")
    asyncio.create_task(_scan_single(city))
    return {"message": f"Scan started for {city}"}


@app.get("/api/routes")
async def list_routes() -> list[dict]:
    return [r.model_dump(mode="json") for r in route_registry.list_routes()]


@app.post("/api/routes", status_code=201)
async def add_route(body: AddRouteBody) -> dict:
    origin = body.origin.strip()
    destination = body.destination.strip()
    if not origin or not destination:
        raise HTTPException(400, "origin and destination must not be empty")
    added = route_registry.add_route(origin, destination, body.route_type)
    if added is None:
        raise HTTPException(409, f"Route '{origin} → {destination}' already monitored")
    await ws_manager.broadcast("route.added", added.model_dump(mode="json"))
    asyncio.create_task(_scan_single_route(added.route_id))
    return added.model_dump(mode="json")


@app.get("/api/routes/{route_id:path}/geometry")
async def route_geometry(route_id: str) -> dict:
    """Return display geometry (list of [lon, lat]) for a route."""
    status = route_registry.get_status(route_id)
    if status is None:
        raise HTTPException(404, f"Route '{route_id}' not found")
    # Prefer cached waypoints from the last scan (avoidance-aware)
    if status.waypoints:
        coords = status.waypoints
    else:
        coords = get_geometry(status.origin, status.destination, status.route_type)
    return {
        "route_id": route_id,
        "route_type": status.route_type,
        "coordinates": coords,
        "avoid_used": status.avoid_used or [],
        "planner_rationale": status.planner_rationale,
    }


@app.post("/api/routes/{route_id:path}/replan")
async def replan_route(route_id: str) -> dict:
    """Clear cached geometry and trigger a fresh route plan."""
    status = route_registry.get_status(route_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")
    updated = status.model_copy(update={"waypoints": None, "planner_rationale": None, "avoid_used": None})
    route_registry.update_status(route_id, updated)
    asyncio.create_task(_scan_single_route(route_id))
    return {"status": "replanning", "route_id": route_id}


@app.delete("/api/routes/{route_id:path}")
async def remove_route(route_id: str) -> dict:
    status = route_registry.get_status(route_id)
    if status is None:
        raise HTTPException(404, f"Route '{route_id}' not found")
    removed = route_registry.remove_route(route_id)
    if not removed:
        raise HTTPException(404, f"Route '{route_id}' not found")
    await ws_manager.broadcast("route.removed", {"route_id": route_id})
    return {"route_id": route_id}


@app.post("/api/routes/scan")
async def scan_all_routes_now() -> dict:
    asyncio.create_task(_scan_all_routes())
    return {"message": "Scan started for all routes"}


@app.post("/api/routes/{route_id:path}/scan")
async def scan_route_now(route_id: str) -> dict:
    if not route_registry.has_route(route_id):
        raise HTTPException(404, f"Route '{route_id}' not monitored")
    asyncio.create_task(_scan_single_route(route_id))
    return {"message": f"Scan started for {route_id}"}


@app.post("/api/analysis/{city}", status_code=202)
async def start_analysis(city: str) -> dict:
    if not registry.has_port(city):
        raise HTTPException(404, f"Port '{city}' not monitored")
    sim_context = simulations.context_for_city(city)
    avoid_polygon = simulations.polygon_for_city(city)
    job_id = await job_store.start_job(city, ws_manager, simulation_context=sim_context, avoid_polygon=avoid_polygon)
    return {"job_id": job_id, "city": city}


@app.get("/api/analysis/{job_id}")
async def get_analysis(job_id: str) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return job.model_dump(mode="json")


@app.get("/api/analysis/{job_id}/map")
async def get_analysis_map(job_id: str) -> FileResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' not found")
    if not job.has_map or not job.map_path or not Path(job.map_path).exists():
        raise HTTPException(404, "Route map not available for this job")
    return FileResponse(job.map_path, media_type="text/html")


@app.get("/api/auto-scan")
async def get_auto_scan() -> dict:
    return {
        "enabled": scheduler.enabled,
        "interval_minutes": scheduler.interval_minutes,
    }


@app.post("/api/auto-scan")
async def set_auto_scan(body: AutoScanBody) -> dict:
    scheduler.configure(body.enabled, body.interval_minutes)
    return {
        "enabled": scheduler.enabled,
        "interval_minutes": scheduler.interval_minutes,
    }


# ── Simulation endpoints ──────────────────────────────────────────────────────

@app.get("/api/simulations")
async def list_simulations() -> list[dict]:
    return [s.model_dump(mode="json") for s in simulations.list()]


@app.get("/api/simulations/event-types")
async def list_event_types() -> list[dict]:
    from backend.simulation import EVENT_DEFAULTS
    return [
        {
            "event_type": et.value,
            "default_severity": defaults["severity"].value,
            "headline": defaults["headline"],
            "hazards": defaults["hazards"],
        }
        for et, defaults in EVENT_DEFAULTS.items()
    ]


@app.post("/api/simulations", status_code=201)
async def create_simulation(body: CreateSimulationBody) -> dict:
    if not body.affected_cities:
        raise HTTPException(400, "affected_cities must not be empty")
    unknown = [c for c in body.affected_cities if not registry.has_port(c)]
    if unknown:
        raise HTTPException(400, f"Unknown port(s): {', '.join(unknown)}")

    event = simulations.create(
        event_type=body.event_type,
        affected_cities=body.affected_cities,
        description=body.description,
        severity=body.severity,
        polygon=body.polygon,
    )
    payload = event.model_dump(mode="json")
    await ws_manager.broadcast("simulation.created", payload)

    # Immediately apply deterministic rules to everything (no LLM, instant)
    await _apply_rules_all_routes()
    await _apply_rules_all_ports()

    # Then kick off full LLM re-scans for directly affected cities/routes
    for city in event.affected_cities:
        asyncio.create_task(_scan_single(city))
    for route in route_registry.list_routes():
        if route.origin in event.affected_cities or route.destination in event.affected_cities:
            asyncio.create_task(_scan_single_route(route.route_id))

    return payload


@app.post("/api/simulations/from-coordinates", status_code=201)
async def create_simulation_from_coordinates(body: CreateCoordSimulationBody) -> dict:
    """
    Create a simulation by dropping an event at geographic coordinates.
    Auto-detects which monitored ports and routes fall within the impact radius.
    """
    all_cities = [p.city for p in registry.list_ports()]
    affected_cities = find_affected_cities(all_cities, body.lat, body.lon, body.radius_km)

    # Detect routes whose path passes through the impact zone
    route_triples = [
        (r.route_id, r.origin, r.destination)
        for r in route_registry.list_routes()
    ]
    affected_route_ids = find_affected_routes(route_triples, body.lat, body.lon, body.radius_km)

    # Build a description if none provided
    description = body.description or (
        f"Event dropped at ({body.lat:.2f}°, {body.lon:.2f}°) "
        f"with {body.radius_km:.0f} km impact radius."
    )

    event = simulations.create(
        event_type=body.event_type,
        affected_cities=affected_cities,
        description=description,
        severity=body.severity,
        coordinates=[body.lat, body.lon],
        radius_km=body.radius_km,
    )
    payload = event.model_dump(mode="json")
    payload["affected_route_ids"] = affected_route_ids
    await ws_manager.broadcast("simulation.created", payload)

    # Immediately apply deterministic rules to ALL routes/ports (instant, no LLM)
    await _apply_rules_all_routes()
    await _apply_rules_all_ports()

    # Then kick off full LLM re-scans for directly affected entities
    for city in affected_cities:
        asyncio.create_task(_scan_single(city))
    for route_id in affected_route_ids:
        asyncio.create_task(_scan_single_route(route_id))

    return payload


@app.delete("/api/simulations/{sim_id}")
async def remove_simulation(sim_id: str) -> dict:
    removed = simulations.remove(sim_id)
    if removed is None:
        raise HTTPException(404, f"Simulation '{sim_id}' not found")
    payload = removed.model_dump(mode="json")
    await ws_manager.broadcast("simulation.removed", payload)

    # Re-scan formerly-affected ports so they return to normal state
    for city in removed.affected_cities:
        asyncio.create_task(_scan_single(city))

    # Re-scan ALL routes — apply_route_rules only escalates, never de-escalates,
    # so any route previously lifted by this sim must be re-assessed from scratch.
    # Scope-limited approaches (endpoint match, radius check) miss polygon events
    # and routes with cities not in CITY_COORDS, so we reset everything.
    route_scanner.clear_cache()
    for route in route_registry.list_routes():
        asyncio.create_task(_scan_single_route(route.route_id))

    return payload


@app.delete("/api/simulations")
async def clear_simulations() -> dict:
    removed = simulations.clear()
    affected = {c for ev in removed for c in ev.affected_cities}
    for ev in removed:
        await ws_manager.broadcast("simulation.removed", ev.model_dump(mode="json"))
    for city in affected:
        asyncio.create_task(_scan_single(city))
    route_scanner.clear_cache()   # nuke entire cache — all sims gone
    for route in route_registry.list_routes():
        if route.origin in affected or route.destination in affected:
            asyncio.create_task(_scan_single_route(route.route_id))
    return {"removed": len(removed)}


@app.post("/api/ports/reset")
async def reset_all_threats() -> dict:
    """Force all ports to LOW risk and kick off a fresh scan."""
    from backend.models import PortStatus as _PortStatus
    for port in registry.list_ports():
        city = port.city
        clean = _PortStatus(city=city, risk_level=RiskLevel.LOW, summary="Awaiting scan")
        registry.update_status(city, clean)
        await ws_manager.broadcast("port.status_updated", {"status": clean.model_dump(mode="json")})
    asyncio.create_task(_scan_all())
    return {"reset": [p.city for p in registry.list_ports()]}


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws_manager.connect(ws)
    try:
        while True:
            # Keep connection alive; commands come via REST
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)


# ── helpers ───────────────────────────────────────────────────────────────────

async def _apply_rules_all_routes() -> None:
    """
    Re-apply deterministic risk rules to every route's *current* stored status.
    No LLM call — purely geometric/sim-state check.
    Broadcasts updates for any route whose risk level changes.
    """
    for route in route_registry.list_routes():
        current = route_registry.get_status(route.route_id)
        if current is None:
            continue
        updated = apply_route_rules(current, simulations)
        if updated.risk_level != current.risk_level:
            route_registry.update_status(route.route_id, updated)
            await ws_manager.broadcast("route.status_updated", updated.model_dump(mode="json"))
            if updated.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                await ws_manager.broadcast("alert.route", updated.model_dump(mode="json"))

async def _apply_rules_all_ports() -> None:
    """Same — re-apply port rules to every current port status."""
    for port in registry.list_ports():
        current = registry.get_status(port.city)
        if current is None:
            continue
        updated = apply_port_rules(current, simulations)
        if updated.risk_level != current.risk_level:
            registry.update_status(port.city, updated)
            await ws_manager.broadcast(
                "port.status_updated",
                {"city": port.city, "status": updated.model_dump(mode="json")},
            )
            if updated.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                await ws_manager.broadcast(
                    "alert.new",
                    {"city": port.city, "status": updated.model_dump(mode="json")},
                )

async def _scan_single_route(route_id: str) -> None:
    route = route_registry.get_status(route_id)
    if route is None:
        return
    try:
        loop = asyncio.get_running_loop()
        sim_context = (
            simulations.context_for_city(route.origin)
            + simulations.context_for_city(route.destination)
            + simulations.context_for_route_geo(route.origin, route.destination)
        )
        status = await loop.run_in_executor(
            None,
            lambda: route_scanner.scan_route(
                route_id, route.origin, route.destination,
                sim_context, route.route_type,
            ),
        )
        # Deterministic override: physical intersection with active events always wins
        status = apply_route_rules(status, simulations)
        route_registry.update_status(route_id, status)
        await ws_manager.broadcast("route.status_updated", status.model_dump(mode="json"))
        if status.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            await ws_manager.broadcast("alert.route", status.model_dump(mode="json"))
    except Exception as e:
        print(f"[API] Route scan error for {route_id}: {e}")


async def _scan_all_routes() -> None:
    for route in route_registry.list_routes():
        await _scan_single_route(route.route_id)


async def _geocode_city(city: str) -> tuple[float, float] | None:
    """Return (lat, lon) for a city name using the free Open-Meteo geocoding API."""
    import json
    from urllib.parse import quote_plus
    from urllib.request import urlopen
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote_plus(city)}&count=1&language=en&format=json"
        loop = asyncio.get_running_loop()
        def _fetch():
            with urlopen(url, timeout=5) as resp:
                return json.loads(resp.read())
        data = await loop.run_in_executor(None, _fetch)
        results = data.get("results") or []
        if results:
            return float(results[0]["latitude"]), float(results[0]["longitude"])
    except Exception:
        pass
    return None


async def _scan_single(city: str) -> None:
    try:
        loop = asyncio.get_running_loop()
        sim_context = simulations.context_for_city(city)

        # Build route context from connected routes
        connected_routes = [
            r for r in route_registry.list_routes()
            if r.origin.lower() == city.lower() or r.destination.lower() == city.lower()
        ]
        route_context = ""
        if connected_routes:
            lines = [f"Route {r.origin}↔{r.destination}: {r.risk_level.value} ({r.summary[:80]})"
                     for r in connected_routes]
            critical = sum(1 for r in connected_routes if r.risk_level.value == "CRITICAL")
            high = sum(1 for r in connected_routes if r.risk_level.value == "HIGH")
            if critical >= 2 or (critical + high) == len(connected_routes) and critical >= 1:
                lines.append(f"→ Port is effectively isolated ({critical} CRITICAL routes)")
            route_context = "\n".join(lines)

        status = await loop.run_in_executor(
            None, scanner.scan_port, city, sim_context, route_context
        )
        # Deterministic overrides
        status = apply_port_rules(status, simulations)
        status = apply_route_propagation(status, city, route_registry)
        # Preserve or fetch coordinates so the map can pin this node
        existing = registry.get_status(city)
        if existing and existing.lat is not None:
            status.lat, status.lon = existing.lat, existing.lon
            if existing.country_code and not status.country_code:
                status = status.model_copy(update={"country_code": existing.country_code})
            if existing.local_news and not status.local_news:
                status = status.model_copy(update={
                    "local_news": existing.local_news,
                    "news_reasoning": existing.news_reasoning,
                })
        else:
            coords = await _geocode_city(city)
            if coords:
                status.lat, status.lon = coords
        registry.update_status(city, status)
        await ws_manager.broadcast(
            "port.status_updated",
            {"city": city, "status": status.model_dump(mode="json")},
        )
        if status.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            await ws_manager.broadcast(
                "alert.new",
                {"city": city, "status": status.model_dump(mode="json")},
            )
        # Non-blocking news analysis (runs after response is sent)
        country_code = status.country_code
        asyncio.create_task(port_news_analyst.analyze_port(city, country_code, registry))
    except Exception as e:
        print(f"[API] Scan error for {city}: {e}")
