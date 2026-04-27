from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from openai import OpenAI

from src.tools.news import get_local_news

if TYPE_CHECKING:
    from backend.port_registry import PortRegistry
    from backend.websocket_manager import ConnectionManager

_CACHE_TTL_SECONDS = 900  # 15 minutes

_NEWS_ANALYST_PROMPT = """\
You are a supply chain news analyst. Review these news headlines from {city} ({country}).

News articles:
{articles}

Which articles are relevant to port operations, shipping, logistics, or supply chain \
disruptions in or near {city}? Rate the overall risk contribution to port operations:
- NONE: no relevant articles
- LOW: minor mentions, no operational impact
- MEDIUM: notable disruptions possible
- HIGH: significant supply chain risk

Respond with ONLY valid JSON:
{{"risk_contribution": "NONE" | "LOW" | "MEDIUM" | "HIGH", "reasoning": "one paragraph"}}"""


class PortNewsAnalyst:
    def __init__(self, ws_manager: ConnectionManager) -> None:
        llm_url = os.environ.get("LLM_URL", "http://localhost:11434")
        api_key = os.environ.get("LLM_API_KEY", "ollama")
        model = os.environ.get("LLM_MODEL", "hermes3:8b")
        self._client = OpenAI(base_url=f"{llm_url}/v1", api_key=api_key)
        self._model = model
        self._ws = ws_manager
        self._cache: dict[str, datetime] = {}

    async def analyze_port(self, city: str, country_code: str | None, port_registry: PortRegistry) -> None:
        cache_key = f"{city}:{country_code}"
        if cache_key in self._cache:
            age = (datetime.now(timezone.utc) - self._cache[cache_key]).total_seconds()
            if age < _CACHE_TTL_SECONDS:
                return

        loop = asyncio.get_running_loop()
        try:
            articles = await loop.run_in_executor(
                None, get_local_news, city, country_code or "", "en", 8
            )
        except Exception:
            articles = []

        if not articles:
            return

        articles_text = "\n".join(
            f"- [{a.get('source', '')}] {a.get('title', '')}: {a.get('summary', '')[:200]}"
            for a in articles[:8]
        )
        prompt = _NEWS_ANALYST_PROMPT.format(
            city=city,
            country=country_code or "unknown",
            articles=articles_text,
        )

        try:
            response = await loop.run_in_executor(
                None,
                lambda: self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=256,
                ),
            )
            raw = response.choices[0].message.content or ""
        except Exception as e:
            print(f"[NewsAnalyst] LLM error for {city}: {e}")
            return

        reasoning = "News analysis unavailable"
        risk_contribution = "NONE"
        try:
            import re
            m = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
            if m:
                data = json.loads(m.group())
                reasoning = data.get("reasoning", reasoning)
                risk_contribution = data.get("risk_contribution", risk_contribution)
        except Exception:
            pass

        # Update registry and broadcast
        status = port_registry.get_status(city)
        if status:
            updated = status.model_copy(update={
                "local_news": articles,
                "news_reasoning": reasoning,
            })
            port_registry.update_status(city, updated)

        await self._ws.broadcast("port.news_updated", {
            "city": city,
            "local_news": articles,
            "news_reasoning": reasoning,
            "news_risk_contribution": risk_contribution,
        })

        self._cache[cache_key] = datetime.now(timezone.utc)
