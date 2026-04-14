"""MCP server exposing the weather tool.

Run standalone:
    python mcp_servers/weather_server.py

The tool name matches the original function name so the orchestrator's
_print_live_data helper can identify it by name.
"""

import sys
import os

# Ensure project root is on the path when the server is launched as a subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP
from src.tools.weather import get_weather as _get_weather

mcp = FastMCP("weather")


@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather conditions for a city.

    Returns a JSON object with: temperature_c, feels_like_c, humidity_pct,
    wind_speed_ms, description, condition_main.
    """
    return _get_weather(city)


if __name__ == "__main__":
    mcp.run()
