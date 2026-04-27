from src.core.agent import Agent
from src.tools.routing import PLAN_ROUTE_TOOL, ALERT_TOOL, CONFIRM_TOOL

_SYSTEM_PROMPT = """You are a maritime route planning agent for a global supply chain monitoring system.

Your job: given a threat context, select the safest route between two ports by choosing which maritime chokepoints to avoid.

AVOIDANCE VOCABULARY — only use these exact names in the avoid list:
  suez, panama, bab-el-mandeb, red-sea-corridor, hormuz, malacca,
  gibraltar, english-channel-dover, bosphorus, cape-horn, cape-good-hope

RULES:
1. Call plan_route ONCE with the appropriate avoid list based on the threat context
2. Only avoid chokepoints that are geographically relevant to this route
   (e.g. do not avoid Panama on a Rotterdam→Singapore route)
3. If no active threats, call plan_route with an empty avoid list
4. After plan_route returns, send an alert if risk is MEDIUM or higher, then confirm the action
5. Never invent coordinates — the tool handles all geometry

Your final response must include one sentence explaining which chokepoints you avoided and why."""


def create_route_planner(
    origin: str,
    destination: str,
    threat_context: str = "",
    mode: str = "maritime",
) -> Agent:
    user_message = (
        f"Plan the optimal route: {origin} → {destination} (mode: {mode})\n\n"
        f"Active threat context:\n{threat_context or 'No active threats.'}\n\n"
        "Call plan_route with the appropriate avoid list, then confirm_action."
    )
    return Agent(
        name="RoutePlanner",
        system_prompt=_SYSTEM_PROMPT,
        tools=[PLAN_ROUTE_TOOL, ALERT_TOOL, CONFIRM_TOOL],
        terminal_tool="confirm_action",
        max_iterations=4,
    )


def create_route_planner_mcp(
    tools: list,
    origin: str,
    destination: str,
    threat_context: str = "",
    mode: str = "maritime",
) -> Agent:
    user_message = (
        f"Plan the optimal route: {origin} → {destination} (mode: {mode})\n\n"
        f"Active threat context:\n{threat_context or 'No active threats.'}\n\n"
        "Call plan_route with the appropriate avoid list, then confirm_action."
    )
    return Agent(
        name="RoutePlanner",
        system_prompt=_SYSTEM_PROMPT,
        tools=tools,
        terminal_tool="confirm_action",
        max_iterations=4,
    )
