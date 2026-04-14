from src.core.agent import Agent
from src.tools.routing import ROUTE_TOOL, ALT_ROUTE_TOOL, ALERT_TOOL, CONFIRM_TOOL

_DEFAULT_ORIGIN = "Veracruz"
_DEFAULT_DESTINATION = "Houston"
SYSTEM_PROMPT_WITH_REROUTE = """You are a supply chain route optimization agent.
Use your tools to reroute affected shipments, then write an action plan.

Call get_route for the given origin/destination. Then call get_alternative_route with an avoid_polygon. Then call send_alert with the appropriate severity. Then call confirm_action.
After all four tool calls complete, write your final action plan covering:
- Original vs alternative route (distance and time)
- Alert issued and action confirmed (Execution OK)
- Suspended maritime routes until the threat passes

Respond in English."""

SYSTEM_PROMPT = """You are a supply chain route optimization agent.
Use your tools to assess the current route and confirm status.

Call get_route for the given origin/destination. Then call confirm_action.
After tool calls complete, write your final action plan covering:
- Current route status (distance and time)
- Action confirmed (Execution OK)

Respond in English."""


def create_route_optimizer_mcp(
    tools: list,
    origin: str = _DEFAULT_ORIGIN,
    destination: str = _DEFAULT_DESTINATION,
    avoid_polygon: list | None = None,
    alert_message: str = "Supply chain route disruption detected",
    alert_severity: str = "CRITICAL",
) -> Agent:
    """Same as create_route_optimizer() but tools come from MCP servers.

    tools — list[Tool] returned by MCPServerConnection.to_tools() for the
            routing server.
    """
    action_id = f"reroute-{origin.lower()}-{destination.lower()}"
    if avoid_polygon is not None:
        forced = [
            {"name": "get_route",             "args": {"origin": origin, "destination": destination}},
            {"name": "get_alternative_route", "args": {"origin": origin, "destination": destination, "avoid_polygon": avoid_polygon}},
            {"name": "send_alert",            "args": {"message": alert_message, "severity": alert_severity}},
            {"name": "confirm_action",        "args": {"action": action_id}},
        ]
        prompt = SYSTEM_PROMPT_WITH_REROUTE
    else:
        forced = [
            {"name": "get_route",     "args": {"origin": origin, "destination": destination}},
            {"name": "confirm_action", "args": {"action": action_id}},
        ]
        prompt = SYSTEM_PROMPT
    return Agent(
        name="RouteOptimizer",
        system_prompt=prompt,
        tools=tools,
        terminal_tool="confirm_action",
        forced_tool_calls=forced,
    )


def create_route_optimizer(
    origin: str = _DEFAULT_ORIGIN,
    destination: str = _DEFAULT_DESTINATION,
    avoid_polygon: list | None = None,
    alert_message: str = "Supply chain route disruption detected",
    alert_severity: str = "CRITICAL",
) -> Agent:
    action_id = f"reroute-{origin.lower()}-{destination.lower()}"
    if avoid_polygon is not None:
        forced = [
            {"name": "get_route",             "args": {"origin": origin, "destination": destination}},
            {"name": "get_alternative_route", "args": {"origin": origin, "destination": destination, "avoid_polygon": avoid_polygon}},
            {"name": "send_alert",            "args": {"message": alert_message, "severity": alert_severity}},
            {"name": "confirm_action",        "args": {"action": action_id}},
        ]
        prompt = SYSTEM_PROMPT_WITH_REROUTE
    else:
        forced = [
            {"name": "get_route",      "args": {"origin": origin, "destination": destination}},
            {"name": "confirm_action", "args": {"action": action_id}},
        ]
        prompt = SYSTEM_PROMPT
    return Agent(
        name="RouteOptimizer",
        system_prompt=prompt,
        tools=[ROUTE_TOOL, ALT_ROUTE_TOOL, ALERT_TOOL, CONFIRM_TOOL],
        terminal_tool="confirm_action",
        forced_tool_calls=forced,
    )
