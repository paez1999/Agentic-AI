from src.core.agent import Agent
from src.tools.weather import WEATHER_TOOL
from src.tools.news import NEWS_TOOL

_DEFAULT_CITIES = ["Veracruz", "Houston", "Tampa"]

SYSTEM_PROMPT = """You are a supply chain risk monitoring agent.
Use your tools to gather real data, then write a risk report.

Call get_weather for each monitored city. Then call get_news with a relevant supply chain risk query.
After all tool calls complete, write your final report covering:
- Severity: LOW / MEDIUM / HIGH / CRITICAL
- Weather conditions per city
- Specific risks identified
- Immediate recommendations

Respond in English."""


def create_risk_monitor_mcp(
    tools: list,
    cities: list[str] | None = None,
    news_query: str = "supply chain disruption port delay",
) -> Agent:
    """Same as create_risk_monitor() but tools come from MCP servers.

    tools — list[Tool] returned by MCPServerConnection.to_tools() for the
            weather and news servers (concatenated).
    """
    resolved_cities = cities or _DEFAULT_CITIES
    city_list = ", ".join(resolved_cities)
    forced = [{"name": "get_weather", "args": {"city": c}} for c in resolved_cities]
    forced.append({"name": "get_news", "args": {"query": news_query}})
    return Agent(
        name="RiskMonitor",
        system_prompt=SYSTEM_PROMPT.replace("each monitored city", city_list),
        tools=tools,
        terminal_tool="get_news",
        forced_tool_calls=forced,
    )


def create_risk_monitor(cities: list[str] | None = None, news_query: str = "supply chain disruption port delay") -> Agent:
    resolved_cities = cities or _DEFAULT_CITIES
    city_list = ", ".join(resolved_cities)
    forced = [{"name": "get_weather", "args": {"city": c}} for c in resolved_cities]
    forced.append({"name": "get_news", "args": {"query": news_query}})
    return Agent(
        name="RiskMonitor",
        system_prompt=SYSTEM_PROMPT.replace("each monitored city", city_list),
        tools=[WEATHER_TOOL, NEWS_TOOL],
        terminal_tool="get_news",
        forced_tool_calls=forced,
    )
