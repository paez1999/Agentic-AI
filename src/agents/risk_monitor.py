from src.core.agent import Agent
from src.tools.weather import WEATHER_TOOL
from src.tools.news import NEWS_TOOL

_DEFAULT_CITIES = ["Veracruz", "Houston", "Tampa"]

SYSTEM_PROMPT = """You are a supply chain risk monitoring agent.
Use your tools to gather real data, then write a risk report.

Call get_weather for each monitored city. Then call get_news with query "hurricane gulf mexico".
After all tool calls complete, write your final report covering:
- Severity: LOW / MEDIUM / HIGH / CRITICAL
- Weather conditions per city
- Specific risks identified
- Immediate recommendations

Respond in English."""


def create_risk_monitor(cities: list[str] | None = None, news_query: str = "hurricane gulf mexico") -> Agent:
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
