from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PortStatus(BaseModel):
    city: str
    risk_level: RiskLevel = RiskLevel.LOW
    summary: str = "Not yet scanned"
    isolated: bool = False
    affected_routes: list[dict] | None = None   # [{"route_id": str, "risk_level": str, "origin": str, "destination": str}]
    local_news: list[dict] | None = None         # [{"title": str, "link": str, "summary": str, "source": str}]
    news_reasoning: str | None = None
    country_code: str | None = None
    weather: dict[str, Any] | None = None
    scanned_at: datetime | None = None
    lat: float | None = None
    lon: float | None = None


class RouteStatus(BaseModel):
    route_id: str
    origin: str
    destination: str
    route_type: str = "maritime"   # maritime | terrestrial | air
    risk_level: RiskLevel = RiskLevel.LOW
    summary: str = "Awaiting scan"
    origin_weather: dict[str, Any] | None = None
    destination_weather: dict[str, Any] | None = None
    scanned_at: datetime | None = None
    waypoints: list[list[float]] | None = None
    planner_rationale: str | None = None
    avoid_used: list[str] | None = None


class FullAnalysisJob(BaseModel):
    job_id: str
    city: str
    status: str = "pending"  # pending | running | completed | failed
    risk_report: str | None = None
    inventory_report: str | None = None
    action_plan: str | None = None
    has_map: bool = False
    map_path: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class WSEvent(BaseModel):
    event: str
    payload: dict[str, Any]


class AutoScanConfig(BaseModel):
    enabled: bool = False
    interval_minutes: int = 15
