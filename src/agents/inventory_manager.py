from src.core.agent import Agent
from src.tools.inventory_db import INVENTORY_TOOL, ROUTES_TOOL

_DEFAULT_CITIES = ["Veracruz", "Houston", "Tampa"]

SYSTEM_PROMPT = """You are a supply chain inventory management agent.
Use your tools to gather real data, then write an inventory impact report.

Call get_inventory for each monitored location. Then call get_active_routes.
After all tool calls complete, write your final report covering:
- At-risk products (name, quantity, USD value) per location
- Compromised routes (id, type, origin→destination, cargo value)
- Estimated delay in days per route
- Total value at risk (USD)

Respond in English."""


def create_inventory_manager_mcp(tools: list, cities: list[str] | None = None) -> Agent:
    """Same as create_inventory_manager() but tools come from MCP servers.

    tools — list[Tool] returned by MCPServerConnection.to_tools() for the
            inventory server.
    """
    resolved_cities = cities or _DEFAULT_CITIES
    city_list = ", ".join(resolved_cities)
    forced = [{"name": "get_inventory", "args": {"location": c}} for c in resolved_cities]
    forced.append({"name": "get_active_routes", "args": {}})
    return Agent(
        name="InventoryManager",
        system_prompt=SYSTEM_PROMPT.replace("each monitored location", city_list),
        tools=tools,
        terminal_tool="get_active_routes",
        forced_tool_calls=forced,
    )


def create_inventory_manager(cities: list[str] | None = None) -> Agent:
    resolved_cities = cities or _DEFAULT_CITIES
    city_list = ", ".join(resolved_cities)
    forced = [{"name": "get_inventory", "args": {"location": c}} for c in resolved_cities]
    forced.append({"name": "get_active_routes", "args": {}})
    return Agent(
        name="InventoryManager",
        system_prompt=SYSTEM_PROMPT.replace("each monitored location", city_list),
        tools=[INVENTORY_TOOL, ROUTES_TOOL],
        terminal_tool="get_active_routes",
        forced_tool_calls=forced,
    )
