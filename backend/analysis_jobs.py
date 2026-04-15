from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

_MAP_DIR = Path("output")

from backend.models import FullAnalysisJob
from backend.orchestrator_factory import create_orchestrator_for_port

if TYPE_CHECKING:
    from backend.simulation import SimulationStore
    from backend.websocket_manager import ConnectionManager


class AnalysisJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, FullAnalysisJob] = {}
        self._event_bus = None
        self._mcp_tools = None

    def get(self, job_id: str) -> FullAnalysisJob | None:
        return self._jobs.get(job_id)

    def list_for_city(self, city: str) -> list[FullAnalysisJob]:
        return [j for j in self._jobs.values() if j.city == city]

    async def start_job(
        self,
        city: str,
        ws_manager: "ConnectionManager",
        simulation_context: str = "",
        avoid_polygon: list[list[float]] | None = None,
    ) -> str:
        job_id = str(uuid.uuid4())[:8]
        job = FullAnalysisJob(
            job_id=job_id,
            city=city,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self._jobs[job_id] = job

        await ws_manager.broadcast("analysis.started", {"job_id": job_id, "city": city})

        asyncio.create_task(self._run_job(job_id, city, ws_manager, simulation_context, avoid_polygon))
        return job_id

    async def _run_job(
        self,
        job_id: str,
        city: str,
        ws_manager: "ConnectionManager",
        simulation_context: str = "",
        avoid_polygon: list[list[float]] | None = None,
    ) -> None:
        job = self._jobs[job_id]
        try:
            orchestrator = create_orchestrator_for_port(
                city,
                simulation_context=simulation_context,
                avoid_polygon=avoid_polygon,
                event_bus=self._event_bus,
                mcp_tools=self._mcp_tools,
            )
            loop = asyncio.get_running_loop()
            scenario_lines = [
                f"Assess supply chain risk and response for the port city: {city}.",
                "Check current weather, news, inventory, and routing.",
            ]
            if simulation_context:
                scenario_lines.append(
                    f"ACTIVE SIMULATED SCENARIO: {simulation_context}"
                )
            scenario = " ".join(scenario_lines)
            map_output_path = str(_MAP_DIR / f"route_map_{job_id}.html")
            report = await loop.run_in_executor(
                None, lambda: orchestrator.run(scenario, map_output_path=map_output_path)
            )
            job.risk_report = report.risk_report.content
            job.inventory_report = report.inventory_report.content
            job.action_plan = report.action_plan.content
            job.map_path = map_output_path if Path(map_output_path).exists() else None
            job.has_map = job.map_path is not None
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            await ws_manager.broadcast(
                "analysis.completed",
                {
                    "job_id": job_id,
                    "city": city,
                    "risk_report": job.risk_report,
                    "inventory_report": job.inventory_report,
                    "action_plan": job.action_plan,
                    "has_map": job.has_map,
                    "map_path": job.map_path,
                    "status": "completed",
                    "completed_at": job.completed_at.isoformat(),
                },
            )
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await ws_manager.broadcast(
                "analysis.failed",
                {"job_id": job_id, "city": city, "error": str(e)},
            )
