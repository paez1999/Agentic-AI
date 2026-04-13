from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from openai import OpenAI

from backend.models import PortStatus, RiskLevel
from src.tools.weather import get_weather
from src.tools.news import get_news

_VALID_LEVELS = {r.value for r in RiskLevel}

_SCANNER_PROMPT = """\
You are a port risk analyst. Given current weather data, recent news, and any active \
simulated scenarios for a port city, classify the risk level.

Weather data:
{weather}

Recent news headlines:
{news}
{simulation}
Respond with ONLY valid JSON, no markdown, no explanation:
{{"risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL", "summary": "one sentence describing the risk"}}

If a simulated event is active, treat it as ground truth and reflect its severity in your \
classification and summary."""


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


class PortRiskScanner:
    def __init__(self) -> None:
        llm_url = os.environ.get("LLM_URL", "http://localhost:11434")
        api_key = os.environ.get("LLM_API_KEY", "ollama")
        model = os.environ.get("LLM_MODEL", "hermes3:8b")
        self._client = OpenAI(base_url=f"{llm_url}/v1", api_key=api_key)
        self._model = model

    def scan_port(self, city: str, simulation_context: str = "") -> PortStatus:
        """Lightweight scan: fetch weather + news, one LLM call, return PortStatus. ~5-10s.

        When simulation_context is non-empty, it is injected into the prompt so the LLM
        factors the simulated scenario into its risk classification.
        """
        weather_raw = get_weather(city)
        news_raw = get_news(f"port {city} weather storm hurricane risk")

        # Parse weather for the status payload
        try:
            weather_data = json.loads(weather_raw)
        except Exception:
            weather_data = {"error": "parse failed"}

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
            f"- [{a.get('source','')}] {a.get('title','')}" for a in articles
        ) or "(no relevant news)"

        sim_block = (
            f"\nActive simulated scenario (authoritative):\n{simulation_context}\n"
            if simulation_context
            else ""
        )
        prompt = _SCANNER_PROMPT.format(
            weather=weather_raw[:800],
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
            print(f"[Scanner] LLM error for {city}: {e}")

        risk_level, summary = _parse_risk_response(raw_text)

        return PortStatus(
            city=city,
            risk_level=risk_level,
            summary=summary,
            weather=weather_data if "error" not in weather_data else None,
            scanned_at=datetime.now(timezone.utc),
        )
