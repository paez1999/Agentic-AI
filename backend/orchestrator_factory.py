from __future__ import annotations

from src.agents.risk_monitor import create_risk_monitor, create_risk_monitor_mcp
from src.agents.inventory_manager import create_inventory_manager, create_inventory_manager_mcp
from src.agents.route_optimizer import create_route_optimizer, create_route_optimizer_mcp
from src.orchestrator import Orchestrator


def create_orchestrator_for_port(
    city: str,
    simulation_context: str = "",
    avoid_polygon: list[list[float]] | None = None,
    event_bus=None,
    mcp_tools: dict | None = None,
) -> Orchestrator:
    """Build an Orchestrator parameterised for a single port city.

    When mcp_tools is provided (dict with keys weather/news/inventory/routing),
    agents are wired to MCP server subprocesses instead of direct Python calls.
    When event_bus is provided, the orchestrator publishes CloudEvents to NATS.
    Falls back to direct-Python tools when mcp_tools is None.
    """
    cities = [city]
    destination = "Houston" if city.lower() != "houston" else "New Orleans"

    orchestrator = Orchestrator.__new__(Orchestrator)
    orchestrator._bus = event_bus

    if mcp_tools is not None:
        weather_news_tools = mcp_tools.get("weather", []) + mcp_tools.get("news", [])
        orchestrator.risk_monitor = create_risk_monitor_mcp(
            tools=weather_news_tools,
            cities=cities,
        )
        orchestrator.inventory_manager = create_inventory_manager_mcp(
            tools=mcp_tools.get("inventory", []),
            cities=cities,
        )
        orchestrator.route_optimizer = create_route_optimizer_mcp(
            tools=mcp_tools.get("routing", []),
            origin=city,
            destination=destination,
            avoid_polygon=avoid_polygon,
        )
    else:
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
