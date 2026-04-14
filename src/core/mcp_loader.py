"""Sync-friendly MCP client loader.

Wraps the async MCP client in a background daemon thread so tool calls from
the synchronous agent loop can reach an MCP server subprocess without
requiring any changes to Agent or Tool.

Usage:
    conn = MCPServerConnection("mcp_servers/weather_server.py")
    tools = conn.to_tools()   # list[Tool] — drop-in replacement
    conn.close()              # shut down server subprocess
"""

import asyncio
import sys
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.tool import Tool


class MCPServerConnection:
    """Maintains a persistent connection to one MCP server subprocess.

    The MCP client is async; this class bridges that into synchronous calls
    by running a dedicated asyncio event loop in a daemon thread and routing
    coroutines to it with asyncio.run_coroutine_threadsafe.
    """

    def __init__(self, server_script: str):
        self._server_script = server_script
        self._session = None
        self._client_cm = None
        self._session_cm = None

        # Dedicated event loop in a daemon thread — lives for the session
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        self._ready = threading.Event()
        future = asyncio.run_coroutine_threadsafe(self._connect(), self._loop)
        try:
            future.result(timeout=30)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to start MCP server '{server_script}': {exc}"
            ) from exc

        if not self._ready.is_set():
            raise TimeoutError(
                f"MCP server '{server_script}' did not become ready within 30 s"
            )

    async def _connect(self) -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=sys.executable,
            args=[self._server_script],
        )
        # Enter the stdio transport context — starts the subprocess
        self._client_cm = stdio_client(params)
        read, write = await self._client_cm.__aenter__()

        # Enter the protocol session context
        self._session_cm = ClientSession(read, write)
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()
        self._ready.set()

    # ------------------------------------------------------------------
    # Sync helpers
    # ------------------------------------------------------------------

    def _run_sync(self, coro, timeout: float = 30):
        """Submit a coroutine to the background loop and block until done."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    def list_tools(self) -> list:
        """Return MCP tool descriptors from the server."""
        return self._run_sync(self._session.list_tools()).tools

    def call_tool(self, name: str, args: dict) -> str:
        """Call a tool on the server and return its text result."""
        result = self._run_sync(self._session.call_tool(name, args))
        if result.content:
            return result.content[0].text
        return ""

    # ------------------------------------------------------------------
    # Tool conversion
    # ------------------------------------------------------------------

    def to_tools(self) -> list["Tool"]:
        """Convert MCP tool descriptors to Tool dataclass objects.

        The returned Tool objects call this MCP connection under the hood,
        so they are drop-in replacements for the direct-function Tool objects
        used in agent factories.
        """
        from src.core.tool import Tool

        tools: list[Tool] = []
        for mt in self.list_tools():
            name = mt.name
            description = mt.description or ""
            # MCP SDK may use inputSchema or input_schema depending on version
            schema = getattr(mt, "inputSchema", None) or getattr(mt, "input_schema", {})

            conn = self

            def make_fn(tool_name: str):
                def fn(**kwargs):
                    return conn.call_tool(tool_name, kwargs)
                return fn

            tools.append(
                Tool(
                    name=name,
                    description=description,
                    parameters=schema,
                    fn=make_fn(name),
                )
            )
        return tools

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Shut down the MCP session and server subprocess."""

        async def _cleanup():
            if self._session_cm is not None:
                try:
                    await self._session_cm.__aexit__(None, None, None)
                except Exception:
                    pass
            if self._client_cm is not None:
                try:
                    await self._client_cm.__aexit__(None, None, None)
                except Exception:
                    pass

        try:
            asyncio.run_coroutine_threadsafe(_cleanup(), self._loop).result(timeout=10)
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)
