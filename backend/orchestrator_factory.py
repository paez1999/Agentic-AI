from __future__ import annotations

from src.agents.risk_monitor import create_risk_monitor
from src.agents.inventory_manager import create_inventory_manager
from src.agents.route_optimizer import create_route_optimizer
from src.orchestrator import Orchestrator


def create_orchestrator_for_port(
    city: str,
    simulation_context: str = "",
    avoid_polygon: list[list[float]] | None = None,
) -> Orchestrator:
    """Build an Orchestrator parameterised for a single port city.

    The risk monitor and inventory manager scan just that city.
    The route optimizer uses city as origin, Houston as destination
    (falls back to a sensible default when city IS Houston).

    When a simulation_context is supplied, it is appended to each agent's
    system prompt so the LLM treats the simulated scenario as ground truth.
    """
    cities = [city]
    destination = "Houston" if city.lower() != "houston" else "New Orleans"

    orchestrator = Orchestrator.__new__(Orchestrator)
    orchestrator._bus = None  # no event bus for per-port jobs
    orchestrator.risk_monitor = create_risk_monitor(cities=cities)
    orchestrator.inventory_manager = create_inventory_manager(cities=cities)
    orchestrator.route_optimizer = create_route_optimizer(
        origin=city,
        destination=destination,
        avoid_polygon=avoid_polygon,
    )

    if simulation_context:
        suffix = (
            "\n\nACTIVE SIMULATED SCENARIO (authoritative — treat as ground truth):\n"
            f"{simulation_context}\n"
            "Factor this scenario into your analysis and response."
        )
        orchestrator.risk_monitor.system_prompt += suffix
        orchestrator.inventory_manager.system_prompt += suffix
        orchestrator.route_optimizer.system_prompt += suffix

    return orchestrator
