import json
import os
import webbrowser
from dataclasses import dataclass
from src.core.agent import AgentResult
from src.agents.risk_monitor import create_risk_monitor
from src.agents.inventory_manager import create_inventory_manager
from src.agents.route_optimizer import create_route_optimizer
from src.tools.map_generator import generate_route_map


def _iter_tool_calls(messages: list[dict]):
    """Yield (tool_name, tool_args_dict, result_str) for every native tool call in messages."""
    # Build a lookup from tool_call_id -> result_str
    result_by_id: dict[str, str] = {
        m["tool_call_id"]: m.get("content", "")
        for m in messages
        if m.get("role") == "tool"
    }
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except Exception:
                args = {}
            result_str = result_by_id.get(tc.get("id", ""), "")
            yield name, args, result_str


def _print_live_data(result: AgentResult) -> None:
    try:
        weather_payloads: list[dict] = []
        news_payloads: list[dict] = []

        for tool_name, _args, result_str in _iter_tool_calls(result.messages):
            try:
                payload = json.loads(result_str)
            except Exception:
                continue
            if tool_name == "get_weather":
                weather_payloads.append(payload)
            elif tool_name == "get_news":
                news_payloads.append(payload)

        if not weather_payloads and not news_payloads:
            return

        border = "=" * 62
        print(f"\n{border}")
        print(f"{'LIVE DATA':^62}")
        print(border)

        if weather_payloads:
            print("WEATHER")
            for w in weather_payloads:
                if "error" in w:
                    continue
                city = w.get("city", "?")
                temp = w.get("temperature_c", "?")
                humidity = w.get("humidity_pct", "?")
                wind = w.get("wind_speed_ms", "?")
                condition = w.get("condition_main") or w.get("description", "?")
                print(f"  {city:<14} {temp:>4}°C  humidity {humidity}%  wind {wind} m/s  {condition}")

        if news_payloads:
            print("NEWS  (top matches)")
            for payload in news_payloads:
                # Handle both formats: top-level list or {articles: [...]}
                if isinstance(payload, list):
                    articles = payload
                elif isinstance(payload, dict):
                    articles = payload.get("articles", [])
                else:
                    articles = []

                for article in articles:
                    source = article.get("source", "")
                    title = article.get("title", "")
                    link = article.get("link", "")
                    prefix = f"[{source}]  " if source else ""
                    print(f"  {prefix}{title}  \u2192  {link}")

        print("=" * 62)
    except Exception:
        pass


def _extract_route_geometries(result: AgentResult) -> dict:
    """Extract geometry arrays from RouteOptimizer's tool responses."""
    geometries: dict = {"original": [], "alternative": [], "risk_polygon": []}
    try:
        for tool_name, tool_args, result_str in _iter_tool_calls(result.messages):
            try:
                payload = json.loads(result_str)
            except Exception:
                continue
            if tool_name == "get_route":
                geometries["original"] = payload.get("geometry", [])
            elif tool_name == "get_alternative_route":
                geometries["alternative"] = payload.get("geometry", [])
                if not geometries["risk_polygon"] and tool_args.get("avoid_polygon"):
                    raw_poly = tool_args["avoid_polygon"]
                    if raw_poly and raw_poly[0] != raw_poly[-1]:
                        raw_poly = raw_poly + [raw_poly[0]]
                    geometries["risk_polygon"] = raw_poly
    except Exception:
        pass
    return geometries


@dataclass
class FinalReport:
    risk_report: AgentResult
    inventory_report: AgentResult
    action_plan: AgentResult

    def summary(self) -> str:
        sep = "=" * 60
        return (
            f"RISK REPORT\n"
            f"{sep}\n"
            f"{self.risk_report.content}\n\n"
            f"{sep}\n"
            f"INVENTORY REPORT\n"
            f"{sep}\n"
            f"{self.inventory_report.content}\n\n"
            f"{sep}\n"
            f"ACTION PLAN\n"
            f"{sep}\n"
            f"{self.action_plan.content}\n"
        )


class Orchestrator:
    def __init__(self):
        self.risk_monitor = create_risk_monitor()
        self.inventory_manager = create_inventory_manager()
        self.route_optimizer = create_route_optimizer()

    def run(self, scenario: str) -> FinalReport:
        print("\n" + "=" * 60)
        print("=== PHASE 1: RISK MONITORING ===")
        print("=" * 60)
        risk_result = self.risk_monitor.run(scenario)
        _print_live_data(risk_result)
        print("\n[RiskMonitor] Report complete.\n")

        print("\n" + "=" * 60)
        print("=== PHASE 2: INVENTORY ASSESSMENT ===")
        print("=" * 60)
        inventory_result = self.inventory_manager.run(risk_result.content)
        print("\n[InventoryManager] Report complete.\n")

        print("\n" + "=" * 60)
        print("=== PHASE 3: ROUTE OPTIMIZATION ===")
        print("=" * 60)
        combined_context = (
            f"RISK REPORT:\n{risk_result.content}\n\n"
            f"INVENTORY REPORT:\n{inventory_result.content}"
        )
        action_result = self.route_optimizer.run(combined_context)
        print("\n[RouteOptimizer] Plan complete.\n")

        # Feature 3: generate route map
        try:
            geos = _extract_route_geometries(action_result)
            if geos["original"] or geos["alternative"]:
                map_path = generate_route_map(
                    original_coords=geos["original"],
                    alt_coords=geos["alternative"],
                    risk_polygon=geos["risk_polygon"],
                    output_path="output/route_map.html",
                )
                print(f"\n[Map] Saved to {map_path}")
                import threading
                threading.Thread(
                    target=webbrowser.open,
                    args=("file://" + map_path,),
                    daemon=True,
                ).start()
        except Exception as e:
            print(f"\n[Map] Skipped: {e}")

        return FinalReport(
            risk_report=risk_result,
            inventory_report=inventory_result,
            action_plan=action_result,
        )
