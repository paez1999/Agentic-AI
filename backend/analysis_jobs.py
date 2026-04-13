from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from backend.models import FullAnalysisJob
from backend.orchestrator_factory import create_orchestrator_for_port

if TYPE_CHECKING:
    from backend.simulation import SimulationStore
    from backend.websocket_manager import ConnectionManager


class AnalysisJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, FullAnalysisJob] = {}

    def get(self, job_id: str) -> FullAnalysisJob | None:
        return self._jobs.get(job_id)

    def list_for_city(self, city: str) -> list[FullAnalysisJob]:
        return [j for j in self._jobs.values() if j.city == city]

    async def start_job(
        self,
        city: str,
        ws_manager: "ConnectionManager",
        simulation_context: str = "",
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

        asyncio.create_task(self._run_job(job_id, city, ws_manager, simulation_context))
        return job_id

    async def _run_job(
        self,
        job_id: str,
        city: str,
        ws_manager: "ConnectionManager",
        simulation_context: str = "",
    ) -> None:
        job = self._jobs[job_id]
        try:
            orchestrator = create_orchestrator_for_port(city, simulation_context=simulation_context)
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
            report = await loop.run_in_executor(None, orchestrator.run, scenario)
            job.risk_report = report.risk_report.content
            job.inventory_report = report.inventory_report.content
            job.action_plan = report.action_plan.content
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
