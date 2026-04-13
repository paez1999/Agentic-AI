from src.core.agent import Agent
from src.tools.routing import ROUTE_TOOL, ALT_ROUTE_TOOL, ALERT_TOOL, CONFIRM_TOOL

_DEFAULT_ORIGIN = "Veracruz"
_DEFAULT_DESTINATION = "Houston"
_DEFAULT_POLYGON = [[-97, 26], [-97, 21], [-90, 21], [-90, 26]]

SYSTEM_PROMPT = """You are a supply chain route optimization agent.
Use your tools to reroute affected shipments, then write an action plan.

Call get_route for the given origin/destination. Then call get_alternative_route with an avoid_polygon. Then call send_alert with the appropriate severity. Then call confirm_action.
After all four tool calls complete, write your final action plan covering:
- Original vs alternative route (distance and time)
- Alert issued and action confirmed (Execution OK)
- Suspended maritime routes until the threat passes

Respond in English."""


def create_route_optimizer(
    origin: str = _DEFAULT_ORIGIN,
    destination: str = _DEFAULT_DESTINATION,
    avoid_polygon: list | None = None,
    alert_message: str = "Hurricane Cat 4 impact on Gulf supply chain routes",
    alert_severity: str = "CRITICAL",
) -> Agent:
    polygon = avoid_polygon if avoid_polygon is not None else _DEFAULT_POLYGON
    action_id = f"reroute-{origin.lower()}-{destination.lower()}"
    return Agent(
        name="RouteOptimizer",
        system_prompt=SYSTEM_PROMPT,
        tools=[ROUTE_TOOL, ALT_ROUTE_TOOL, ALERT_TOOL, CONFIRM_TOOL],
        terminal_tool="confirm_action",
        forced_tool_calls=[
            {"name": "get_route",            "args": {"origin": origin, "destination": destination}},
            {"name": "get_alternative_route", "args": {"origin": origin, "destination": destination, "avoid_polygon": polygon}},
            {"name": "send_alert",           "args": {"message": alert_message, "severity": alert_severity}},
            {"name": "confirm_action",       "args": {"action": action_id}},
        ],
    )
