"""MCP server exposing inventory / ERP tools.

Run standalone:
    python mcp_servers/inventory_server.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP
from src.tools.inventory_db import init_db, get_inventory as _get_inventory, get_active_routes as _get_active_routes

# Initialize DB connection (or fall back to mock) when the server starts
init_db()

mcp = FastMCP("inventory")


@mcp.tool()
def get_inventory(location: str) -> str:
    """Get inventory levels at a distribution center.

    Available locations: Veracruz, Houston, Tampa.
    Returns a JSON object with center name, location, and a list of products
    (name, category, stock_units, value_usd).
    """
    return _get_inventory(location)


@mcp.tool()
def get_active_routes() -> str:
    """Get all active supply chain routes.

    Returns a JSON list of routes with id, type, origin, destination, carrier,
    eta_days, cargo_value_usd, and status.
    """
    return _get_active_routes()


if __name__ == "__main__":
    mcp.run()
