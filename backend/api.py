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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.analysis_jobs import AnalysisJobStore
from backend.models import AutoScanConfig, PortStatus, RiskLevel
from backend.port_registry import PortRegistry
from backend.scanner import PortRiskScanner
from backend.scheduler import AutoScanScheduler
from backend.simulation import EventType, SimulationStore
from backend.websocket_manager import ConnectionManager
from src.tools.inventory_db import init_db


# ── singletons ────────────────────────────────────────────────────────────────

registry = PortRegistry()
ws_manager = ConnectionManager()
scanner = PortRiskScanner()
job_store = AnalysisJobStore()
simulations = SimulationStore()
auto_scan_config = AutoScanConfig()


async def _scan_all() -> None:
    """Scan every monitored port and broadcast results."""
    for port_status in registry.list_ports():
        await _scan_single(port_status.city)


scheduler = AutoScanScheduler(scan_all_fn=_scan_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
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


class CreateSimulationBody(BaseModel):
    event_type: EventType
    affected_cities: list[str]
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


@app.post("/api/analysis/{city}", status_code=202)
async def start_analysis(city: str) -> dict:
    if not registry.has_port(city):
        raise HTTPException(404, f"Port '{city}' not monitored")
    sim_context = simulations.context_for_city(city)
    job_id = await job_store.start_job(city, ws_manager, simulation_context=sim_context)
    return {"job_id": job_id, "city": city}


@app.get("/api/analysis/{job_id}")
async def get_analysis(job_id: str) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return job.model_dump(mode="json")


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
    )
    payload = event.model_dump(mode="json")
    await ws_manager.broadcast("simulation.created", payload)

    # Re-scan affected ports so they reflect the new scenario
    for city in event.affected_cities:
        asyncio.create_task(_scan_single(city))

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

    return payload


@app.delete("/api/simulations")
async def clear_simulations() -> dict:
    removed = simulations.clear()
    affected = {c for ev in removed for c in ev.affected_cities}
    for ev in removed:
        await ws_manager.broadcast("simulation.removed", ev.model_dump(mode="json"))
    for city in affected:
        asyncio.create_task(_scan_single(city))
    return {"removed": len(removed)}


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

async def _scan_single(city: str) -> None:
    try:
        loop = asyncio.get_running_loop()
        sim_context = simulations.context_for_city(city)
        status = await loop.run_in_executor(
            None, scanner.scan_port, city, sim_context
        )
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
    except Exception as e:
        print(f"[API] Scan error for {city}: {e}")
