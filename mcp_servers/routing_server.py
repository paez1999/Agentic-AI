"""MCP server exposing routing / TMS tools.

Run standalone:
    python mcp_servers/routing_server.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP
from src.tools.routing import (
    get_route as _get_route,
    get_alternative_route as _get_alternative_route,
    send_alert as _send_alert,
    confirm_action as _confirm_action,
)

mcp = FastMCP("routing")


@mcp.tool()
def get_route(origin: str, destination: str) -> str:
    """Get the current route between two cities via OpenRouteService.

    Returns JSON with distance_km, duration_hours, and geometry coordinates.
    """
    return _get_route(origin, destination)


@mcp.tool()
def get_alternative_route(origin: str, destination: str, avoid_polygon: list) -> str:
    """Get an alternative route that avoids a geographic risk polygon.

    avoid_polygon is a list of [lon, lat] coordinate pairs defining the exclusion zone.
    Returns JSON with distance_km, duration_hours, and geometry coordinates.
    """
    return _get_alternative_route(origin, destination, avoid_polygon)


@mcp.tool()
def send_alert(message: str, severity: str) -> str:
    """Send a supply chain risk alert.

    severity must be one of: LOW, MEDIUM, HIGH, CRITICAL.
    Returns a JSON confirmation with timestamp and alert id.
    """
    return _send_alert(message, severity)


@mcp.tool()
def confirm_action(action: str) -> str:
    """Record a decision and confirm its execution.

    Returns a JSON object with status 'Execution OK' and the recorded action.
    """
    return _confirm_action(action)


@mcp.tool()
def plan_route(
    origin: str,
    destination: str,
    mode: str = "maritime",
    avoid: list = [],
) -> str:
    """Plan an optimal route between two ports/cities.

    mode: 'maritime' (ocean corridors), 'air' (great circle), or 'terrestrial' (road).
    avoid: list of chokepoint names to route around — valid values:
      suez, panama, bab-el-mandeb, red-sea-corridor, hormuz, malacca,
      gibraltar, english-channel-dover, bosphorus, cape-horn, cape-good-hope.
    Returns JSON with waypoints, chokepoints_crossed, distance_km, avoid_applied.
    """
    import json
    from backend import route_planner as _route_planner
    result = _route_planner.plan(origin, destination, mode, avoid)
    return json.dumps(result)


if __name__ == "__main__":
    mcp.run()
