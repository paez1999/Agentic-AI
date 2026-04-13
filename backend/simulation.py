from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.models import RiskLevel


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


class SimulationEvent(BaseModel):
    sim_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    event_type: EventType
    severity: RiskLevel
    affected_cities: list[str]
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def context_for(self, city: str) -> str | None:
        """Produce injected scenario text for an affected city, else None."""
        if city not in self.affected_cities:
            return None
        defaults = EVENT_DEFAULTS.get(self.event_type, {})
        hazards = defaults.get("hazards", "severe disruption")
        return (
            f"[SIMULATED EVENT · {self.event_type.value} · severity {self.severity.value}] "
            f"Affecting {city} and surrounding region. "
            f"Hazards: {hazards}. "
            f"Description: {self.description}"
        )


class SimulationStore:
    def __init__(self) -> None:
        self._events: dict[str, SimulationEvent] = {}

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

    def events_affecting(self, city: str) -> list[SimulationEvent]:
        return [ev for ev in self._events.values() if city in ev.affected_cities]

    # ── mutations ────────────────────────────────────────────────────────────

    def create(
        self,
        event_type: EventType,
        affected_cities: list[str],
        description: str | None = None,
        severity: RiskLevel | None = None,
    ) -> SimulationEvent:
        defaults = EVENT_DEFAULTS.get(event_type, {})
        resolved_severity = severity or defaults.get("severity", RiskLevel.HIGH)
        resolved_description = description or defaults.get("headline", "Simulated event")
        event = SimulationEvent(
            event_type=event_type,
            severity=resolved_severity,
            affected_cities=[c for c in affected_cities if c],
            description=resolved_description,
        )
        self._events[event.sim_id] = event
        return event

    def remove(self, sim_id: str) -> SimulationEvent | None:
        return self._events.pop(sim_id, None)

    def clear(self) -> list[SimulationEvent]:
        removed = list(self._events.values())
        self._events.clear()
        return removed
