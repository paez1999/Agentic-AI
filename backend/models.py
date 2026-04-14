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
    weather: dict[str, Any] | None = None
    scanned_at: datetime | None = None


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
