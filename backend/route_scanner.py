from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from openai import OpenAI

from backend.models import RouteStatus, RiskLevel
from src.tools.weather import get_weather
from src.tools.news import get_news

_VALID_LEVELS = {r.value for r in RiskLevel}

_ROUTE_SCANNER_PROMPT = """\
You are a supply chain route risk analyst. Given weather at origin and destination, \
recent news, and any active simulated scenarios, classify the risk level for this route.

Route: {origin} → {destination}
Transport mode: {route_type}

Origin weather ({origin}):
{origin_weather}

Destination weather ({destination}):
{dest_weather}

Recent news headlines:
{news}
{simulation}
Respond with ONLY valid JSON, no markdown, no explanation:
{{"risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL", "summary": "one sentence describing the route risk"}}

Consider risks appropriate to the transport mode:
- maritime: storm systems, port closures, piracy, shipping lane disruptions
- terrestrial: road/rail closures, border crossings, landslides, civil unrest
- air: airspace restrictions, extreme weather, airport closures, geopolitical overflight bans
If a simulated event is active, treat it as ground truth."""


def _parse_risk_response(text: str) -> tuple[RiskLevel, str]:
    """Extract risk_level + summary from LLM response. Falls back to LOW on failure."""
    try:
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            level_str = str(data.get("risk_level", "")).upper()
            if level_str in _VALID_LEVELS:
                return RiskLevel(level_str), str(data.get("summary", "No summary available"))
    except Exception:
        pass
    return RiskLevel.LOW, "Assessment unavailable"


class RouteRiskScanner:
    def __init__(self) -> None:
        llm_url = os.environ.get("LLM_URL", "http://localhost:11434")
        api_key = os.environ.get("LLM_API_KEY", "ollama")
        model = os.environ.get("LLM_MODEL", "hermes3:8b")
        self._client = OpenAI(base_url=f"{llm_url}/v1", api_key=api_key)
        self._model = model
        self._cache: dict[str, tuple[RouteStatus, datetime]] = {}

    def clear_cache(self, route_id: str | None = None) -> None:
        """Evict one or all entries from the scan cache."""
        if route_id is None:
            self._cache.clear()
        else:
            self._cache.pop(route_id, None)

    def scan_route(
        self,
        route_id: str,
        origin: str,
        destination: str,
        simulation_context: str = "",
        route_type: str = "maritime",
    ) -> RouteStatus:
        """Scan a route: fetch weather for both endpoints + news, one LLM call, return RouteStatus.

        When simulation_context is non-empty the cache is bypassed and the scenario
        is injected into the prompt as authoritative ground truth.
        """
        if not simulation_context and route_id in self._cache:
            cached_status, cached_at = self._cache[route_id]
            if (datetime.now(timezone.utc) - cached_at).total_seconds() < 300:
                return cached_status

        origin_weather_raw = get_weather(origin)
        dest_weather_raw = get_weather(destination)
        news_raw = get_news(
            f"maritime shipping {origin} {destination} weather storm disruption port risk"
        )

        # Parse weather for the status payload
        try:
            origin_weather_data = json.loads(origin_weather_raw)
        except Exception:
            origin_weather_data = {"error": "parse failed"}

        try:
            dest_weather_data = json.loads(dest_weather_raw)
        except Exception:
            dest_weather_data = {"error": "parse failed"}

        # Truncate news to top 3 articles for the prompt
        try:
            news_data = json.loads(news_raw)
            if isinstance(news_data, list):
                articles = news_data[:3]
            elif isinstance(news_data, dict):
                articles = news_data.get("articles", [])[:3]
            else:
                articles = []
        except Exception:
            articles = []

        news_summary = "\n".join(
            f"- [{a.get('source', '')}] {a.get('title', '')}" for a in articles
        ) or "(no relevant news)"

        sim_block = (
            f"\nActive simulated scenario (authoritative):\n{simulation_context}\n"
            if simulation_context
            else ""
        )

        prompt = _ROUTE_SCANNER_PROMPT.format(
            origin=origin,
            destination=destination,
            route_type=route_type,
            origin_weather=origin_weather_raw[:600],
            dest_weather=dest_weather_raw[:600],
            news=news_summary,
            simulation=sim_block,
        )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=128,
            )
            raw_text = response.choices[0].message.content or ""
        except Exception as e:
            raw_text = ""
            print(f"[RouteScanner] LLM error for {route_id}: {e}")

        risk_level, summary = _parse_risk_response(raw_text)

        # Derive chokepoints to avoid from simulation context
        _CHOKEPOINTS = [
            "suez", "panama", "bab-el-mandeb", "red-sea-corridor", "hormuz",
            "malacca", "gibraltar", "english-channel-dover", "bosphorus",
            "cape-horn", "cape-good-hope",
        ]
        ctx_lower = (simulation_context or "").lower()
        avoid = [cp for cp in _CHOKEPOINTS if cp in ctx_lower or cp.replace("-", " ") in ctx_lower]

        # Plan geometry with avoidance
        try:
            from backend import route_planner
            plan_result = route_planner.plan(origin, destination, mode=route_type, avoid=avoid)
            waypoints = plan_result.get("waypoints") or None
            avoid_used = plan_result.get("avoid_applied") or None
        except Exception as e:
            print(f"[RouteScanner] route_planner error for {route_id}: {e}")
            waypoints = None
            avoid_used = None

        if not waypoints:
            planner_rationale = "Route planning failed — using fallback geometry."
        elif avoid_used:
            planner_rationale = f"Avoiding {', '.join(avoid_used)} due to active simulation context."
        else:
            planner_rationale = "Direct route — no active threat avoidance."

        status = RouteStatus(
            route_id=route_id,
            origin=origin,
            destination=destination,
            route_type=route_type,
            risk_level=risk_level,
            summary=summary,
            origin_weather=origin_weather_data if "error" not in origin_weather_data else None,
            destination_weather=dest_weather_data if "error" not in dest_weather_data else None,
            scanned_at=datetime.now(timezone.utc),
            waypoints=waypoints,
            avoid_used=avoid_used,
            planner_rationale=planner_rationale,
        )

        if not simulation_context:
            self._cache[route_id] = (status, datetime.now(timezone.utc))

        return status
