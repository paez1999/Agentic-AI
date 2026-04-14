import os
import sys

# Force UTF-8 output on Windows (cp1252 can't encode model's Unicode output)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from src.tools.inventory_db import init_db
import httpx
from src.orchestrator import Orchestrator

SCENARIO = """
Monitor current supply chain conditions for distribution centers
in Veracruz, Houston, and Tampa. Assess any active risks and recommend actions.
"""

# 1. Update the model name to match exactly what Ollama uses
MODEL = "hermes3:8b"


def check_server() -> None:
    # 2. Change the default port to 11434 (Ollama's port)
    url = os.environ.get("LLM_URL", "http://localhost:11434")
    try:
        # Ollama's OpenAI-compatible endpoint
        httpx.get(f"{url}/v1/models", timeout=3)
    except Exception:
        # 3. Update the error message for Ollama
        print(f"[ERROR] Ollama server not reachable at {url}")
        print()
        print("Start it with:")
        print(f"  ollama run {MODEL}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("MULTI-AGENT SUPPLY CHAIN SYSTEM")
    print("PoC - Risk Detection and Response")
    print("=" * 60)
    print(f"\nScenario: {SCENARIO.strip()}\n")

    check_server()
    init_db()

    orchestrator = Orchestrator()
    try:
        report = orchestrator.run(SCENARIO)
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        raise SystemExit(1)

    print("\n" + "=" * 60)
    print("CONSOLIDATED FINAL REPORT")
    print("=" * 60)
    print(report.summary())


if __name__ == "__main__":
    main()
