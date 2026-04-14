"""Entry point that runs the supply-chain pipeline using MCP servers.

Each tool (weather, news, inventory, routing) is served by a dedicated MCP
server subprocess.  Agents connect to their servers via stdio transport and
call tools through the Model Context Protocol instead of direct Python calls.

Usage:
    python main_mcp.py

The original direct-function mode is still available via:
    python main.py
"""

import os
import sys

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

import httpx

from src.tools.inventory_db import init_db
from src.core.event_bus import EventBus
from src.core.mcp_loader import MCPServerConnection
from src.agents.risk_monitor import create_risk_monitor_mcp
from src.agents.inventory_manager import create_inventory_manager_mcp
from src.agents.route_optimizer import create_route_optimizer_mcp
from src.orchestrator import Orchestrator

SCENARIO = """
Monitor current supply chain conditions for distribution centers
in Veracruz, Houston, and Tampa. Assess any active risks and recommend actions.
"""

MODEL = "hermes3:8b"

# Paths to MCP server scripts (relative to project root)
MCP_SERVERS = {
    "weather":   "mcp_servers/weather_server.py",
    "news":      "mcp_servers/news_server.py",
    "inventory": "mcp_servers/inventory_server.py",
    "routing":   "mcp_servers/routing_server.py",
}


def check_server() -> None:
    url = os.environ.get("LLM_URL", "http://localhost:11434")
    try:
        httpx.get(f"{url}/v1/models", timeout=3)
    except Exception:
        print(f"[ERROR] Ollama server not reachable at {url}")
        print()
        print("Start it with:")
        print(f"  ollama run {MODEL}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("MULTI-AGENT SUPPLY CHAIN SYSTEM  [MCP mode]")
    print("PoC - Risk Detection and Response")
    print("=" * 60)
    print(f"\nScenario: {SCENARIO.strip()}\n")

    check_server()
    init_db()

    bus = EventBus()

    def _on_event(subject: str, envelope: dict) -> None:
        event_type = envelope.get("type", subject)
        time = envelope.get("time", "")[:19]
        print(f"\n[NATS] ◀ {subject}  type={event_type}  time={time}")

    bus.subscribe("supply_chain.>", _on_event)

    print("[MCP] Starting server subprocesses…")
    conns: dict[str, MCPServerConnection] = {}
    try:
        for name, script in MCP_SERVERS.items():
            print(f"  • {name} ({script})")
            conns[name] = MCPServerConnection(script)
        print("[MCP] All servers ready.\n")

        risk_monitor = create_risk_monitor_mcp(
            tools=conns["weather"].to_tools() + conns["news"].to_tools(),
        )
        inv_manager = create_inventory_manager_mcp(
            tools=conns["inventory"].to_tools(),
        )
        route_opt = create_route_optimizer_mcp(
            tools=conns["routing"].to_tools(),
        )

        orchestrator = Orchestrator(
            risk_monitor=risk_monitor,
            inventory_manager=inv_manager,
            route_optimizer=route_opt,
            event_bus=bus,
        )

        try:
            report = orchestrator.run(SCENARIO)
        except Exception as e:
            print(f"\n[ERROR] Pipeline failed: {e}")
            raise SystemExit(1)

        print("\n" + "=" * 60)
        print("CONSOLIDATED FINAL REPORT")
        print("=" * 60)
        print(report.summary())

    finally:
        bus.close()
        print("\n[MCP] Shutting down server subprocesses…")
        for name, conn in conns.items():
            try:
                conn.close()
                print(f"  • {name} closed")
            except Exception as exc:
                print(f"  • {name} close error: {exc}")


if __name__ == "__main__":
    main()
