"""MCP server exposing the news / RSS aggregation tool.

Run standalone:
    python mcp_servers/news_server.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP
from src.tools.news import get_news as _get_news

mcp = FastMCP("news")


@mcp.tool()
def get_news(query: str) -> str:
    """Search supply chain and weather news across multiple RSS feeds.

    Fans out across BBC World, GDACS disaster alerts, National Hurricane Center,
    and Reuters. Returns a JSON list of matching articles with title, summary,
    published date, link, and source.
    """
    return _get_news(query)


if __name__ == "__main__":
    mcp.run()
