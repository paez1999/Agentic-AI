from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from backend.models import RiskLevel

_SIMULATIONS_PATH = Path(__file__).parent / "data" / "simulations.json"


class EventType(str, Enum):
    HURRICANE = "HURRICANE"
    EARTHQUAKE = "EARTHQUAKE"
    TSUNAMI = "TSUNAMI"
    WILDFIRE = "WILDFIRE"
    FLOOD = "FLOOD"
    VOLCANIC_ERUPTION = "VOLCANIC_ERUPTION"
    NUCLEAR_STRIKE = "NUCLEAR_STRIKE"
    CYBERATTACK = "CYBERATTACK"
    PORT_STRIKE = "PORT_STRIKE"
    ARMED_CONFLICT = "ARMED_CONFLICT"
    PANDEMIC = "PANDEMIC"
    CUSTOM = "CUSTOM"


# Mapping of event type → sensible default risk level, short description, and the kind of
# hazard the agents should reason about. The severity can be overridden at creation time.
EVENT_DEFAULTS: dict[EventType, dict[str, Any]] = {
    EventType.HURRICANE: {
        "severity": RiskLevel.CRITICAL,
        "headline": "Category 4+ hurricane making landfall",
        "hazards": "storm surge, 200+ km/h winds, flooding, port closure",
    },
    EventType.EARTHQUAKE: {
        "severity": RiskLevel.HIGH,
        "headline": "Magnitude 7.2 earthquake",
        "hazards": "structural damage, infrastructure collapse, aftershocks",
    },
    EventType.TSUNAMI: {
        "severity": RiskLevel.CRITICAL,
        "headline": "Tsunami wave approaching coast",
        "hazards": "coastal flooding, port facilities destroyed, mass evacuation",
    },
    EventType.WILDFIRE: {
        "severity": RiskLevel.HIGH,
        "headline": "Uncontained wildfire near port facilities",
        "hazards": "smoke closure, evacuation, road blockage",
    },
    EventType.FLOOD: {
        "severity": RiskLevel.HIGH,
        "headline": "Severe flooding in port district",
        "hazards": "loading docks inoperable, transport network cut",
    },
    EventType.VOLCANIC_ERUPTION: {
        "severity": RiskLevel.HIGH,
        "headline": "Volcanic eruption with ash cloud",
        "hazards": "air/sea traffic shutdown, ash contamination",
    },
    EventType.NUCLEAR_STRIKE: {
        "severity": RiskLevel.CRITICAL,
        "headline": "Nuclear detonation in region",
        "hazards": "blast damage, radiation contamination, total port denial",
    },
    EventType.CYBERATTACK: {
        "severity": RiskLevel.HIGH,
        "headline": "Ransomware attack on port systems",
        "hazards": "terminal operating system offline, customs paralysed",
    },
    EventType.PORT_STRIKE: {
        "severity": RiskLevel.MEDIUM,
        "headline": "Dockworkers on strike",
        "hazards": "loading operations halted indefinitely",
    },
    EventType.ARMED_CONFLICT: {
        "severity": RiskLevel.CRITICAL,
        "headline": "Armed conflict in region",
        "hazards": "shipping lanes unsafe, sanctions risk, workforce displacement",
    },
    EventType.PANDEMIC: {
        "severity": RiskLevel.HIGH,
        "headline": "Disease outbreak forcing quarantine",
        "hazards": "workforce shortage, mandatory ship quarantines",
    },
    EventType.CUSTOM: {
        "severity": RiskLevel.MEDIUM,
        "headline": "Custom event",
        "hazards": "see description",
    },
}


# Risk-zone polygons (lon, lat) for hurricane events, keyed by affected city.
# Each polygon covers the dangerous sea/coastal area near that port that
# routing should avoid when a hurricane is active.
HURRICANE_POLYGONS: dict[str, list[list[float]]] = {
    "Veracruz": [[-97, 17], [-97, 22], [-92, 22], [-92, 17], [-97, 17]],
    "Houston":  [[-97, 26], [-97, 30], [-93, 30], [-93, 26], [-97, 26]],
    "Tampa":    [[-84, 24], [-84, 28], [-80, 28], [-80, 24], [-84, 24]],
    "Panama":   [[-81,  7], [-81, 10], [-77, 10], [-77,  7], [-81,  7]],
}


class SimulationEvent(BaseModel):
    sim_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    event_type: EventType
    severity: RiskLevel
    affected_cities: list[str]
    description: str
    polygon: list[list[float]] | None = None
    # Coordinate-drop fields (set when simulation is created via map drop)
    coordinates: list[float] | None = None   # [lat, lon]
    radius_km: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def context_for(self, city: str) -> str | None:
        """Produce injected scenario text for an affected city, else None."""
        if city not in self.affected_cities:
            return None
        defaults = EVENT_DEFAULTS.get(self.event_type, {})
        hazards = defaults.get("hazards", "severe disruption")
        geo_note = ""
        if self.coordinates:
            lat, lon = self.coordinates
            geo_note = f" Event epicentre at ({lat:.2f}°, {lon:.2f}°), impact radius {self.radius_km or '?'} km."
        return (
            f"[SIMULATED EVENT · {self.event_type.value} · severity {self.severity.value}] "
            f"Affecting {city} and surrounding region.{geo_note} "
            f"Hazards: {hazards}. "
            f"Description: {self.description}"
        )

    def context_for_route(self, origin: str, destination: str) -> str | None:
        """
        Return scenario context for a route that passes through this event's
        impact zone (coordinate-drop simulations only).
        """
        if self.coordinates is None:
            return None
        defaults = EVENT_DEFAULTS.get(self.event_type, {})
        hazards = defaults.get("hazards", "severe disruption")
        lat, lon = self.coordinates
        return (
            f"[SIMULATED EVENT · {self.event_type.value} · severity {self.severity.value}] "
            f"Route {origin}→{destination} passes through event impact zone "
            f"(epicentre {lat:.2f}°, {lon:.2f}°, radius {self.radius_km or '?'} km). "
            f"Hazards: {hazards}. "
            f"Description: {self.description}"
        )


class SimulationStore:
    def __init__(self) -> None:
        self._events: dict[str, SimulationEvent] = {}
        self._load()

    def _load(self) -> None:
        if not _SIMULATIONS_PATH.exists():
            return
        try:
            raw = json.loads(_SIMULATIONS_PATH.read_text())
            for item in raw:
                ev = SimulationEvent.model_validate(item)
                self._events[ev.sim_id] = ev
        except Exception:
            pass  # corrupt file — start empty

    def _save(self) -> None:
        _SIMULATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = [ev.model_dump(mode="json") for ev in self._events.values()]
        _SIMULATIONS_PATH.write_text(json.dumps(data, indent=2))

    # ── queries ──────────────────────────────────────────────────────────────

    def list(self) -> list[SimulationEvent]:
        return list(self._events.values())

    def get(self, sim_id: str) -> SimulationEvent | None:
        return self._events.get(sim_id)

    def affected_cities(self) -> set[str]:
        affected: set[str] = set()
        for ev in self._events.values():
            affected.update(ev.affected_cities)
        return affected

    def context_for_city(self, city: str) -> str:
        """Concatenate all simulation context lines relevant to this city."""
        lines = [
            ctx
            for ev in self._events.values()
            if (ctx := ev.context_for(city)) is not None
        ]
        return "\n".join(lines)

    def context_for_route_geo(self, origin: str, destination: str) -> str:
        """
        Return combined scenario context for a route that passes through any
        active coordinate-drop simulation's impact zone.
        """
        lines = [
            ctx
            for ev in self._events.values()
            if (ctx := ev.context_for_route(origin, destination)) is not None
        ]
        return "\n".join(lines)

    def polygon_for_city(self, city: str) -> list[list[float]] | None:
        """Return the polygon of the first active simulation affecting this city."""
        for ev in self._events.values():
            if city in ev.affected_cities and ev.polygon is not None:
                return ev.polygon
        return None

    def events_affecting(self, city: str) -> list[SimulationEvent]:
        return [ev for ev in self._events.values() if city in ev.affected_cities]

    # ── mutations ────────────────────────────────────────────────────────────

    def create(
        self,
        event_type: EventType,
        affected_cities: list[str],
        description: str | None = None,
        severity: RiskLevel | None = None,
        polygon: list[list[float]] | None = None,
        coordinates: list[float] | None = None,
        radius_km: float | None = None,
    ) -> SimulationEvent:
        defaults = EVENT_DEFAULTS.get(event_type, {})
        resolved_severity = severity or defaults.get("severity", RiskLevel.HIGH)
        resolved_description = description or defaults.get("headline", "Simulated event")

        # Auto-assign hurricane polygon based on first matching affected city
        if polygon is None and event_type == EventType.HURRICANE:
            for city in affected_cities:
                if city in HURRICANE_POLYGONS:
                    polygon = HURRICANE_POLYGONS[city]
                    break

        event = SimulationEvent(
            event_type=event_type,
            severity=resolved_severity,
            affected_cities=[c for c in affected_cities if c],
            description=resolved_description,
            polygon=polygon,
            coordinates=coordinates,
            radius_km=radius_km,
        )
        self._events[event.sim_id] = event
        self._save()
        return event

    def remove(self, sim_id: str) -> SimulationEvent | None:
        ev = self._events.pop(sim_id, None)
        if ev is not None:
            self._save()
        return ev

    def clear(self) -> list[SimulationEvent]:
        removed = list(self._events.values())
        self._events.clear()
        self._save()
        return removed
