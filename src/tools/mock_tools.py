"""Hybrid integrations for external systems/APIs.

Agent 1 and Agent 3 use free online sources (no paid API keys).
Agent 2 keeps static inventory values.
"""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

import requests


def _safe_get_json(url: str, timeout_seconds: int = 4) -> dict | None:
    """Return JSON from a URL or None if request fails."""
    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def _severity_from_signals(wind_speed_kmh: float, alert_hits: int) -> str:
    if wind_speed_kmh >= 50 or alert_hits >= 5:
        return "high"
    if wind_speed_kmh >= 30 or alert_hits >= 2:
        return "medium"
    return "low"


def _region_keywords(region: str) -> str:
    region_map = {
        "Global": "global maritime trade disruption",
        "Middle East": "Middle East Strait of Hormuz Gulf shipping",
        "Red Sea": "Red Sea Bab el-Mandeb Suez Canal shipping attacks",
        "Europe": "Europe port strikes sanctions shipping",
        "East Asia": "Taiwan Strait East China Sea port disruption",
        "South China Sea": "South China Sea maritime tension shipping lanes",
        "Black Sea": "Black Sea maritime corridor conflict shipping",
        "North America": "US Canada port strike rail logistics disruption",
        "Latin America": "Panama Canal Latin America port disruption",
    }
    return region_map.get(region, region_map["Global"])


def _fetch_gdelt_articles(query: str, max_records: int = 8) -> list[dict]:
    gdelt_url = (
        "https://api.gdeltproject.org/api/v2/doc/doc"
        f"?query={quote_plus(query)}&mode=ArtList&maxrecords={max_records}&format=json"
    )
    gdelt_payload = _safe_get_json(gdelt_url)
    return gdelt_payload.get("articles", []) if gdelt_payload else []


def _fallback_coordinates_from_name(place_name: str) -> tuple[float, float]:
    """Generate deterministic fallback coordinates when geocoding is unavailable."""
    seed = sum(ord(ch) for ch in place_name)
    lat = ((seed % 120) - 60) * 0.9
    lon = ((seed % 300) - 150) * 1.1
    return float(lat), float(lon)


def _resolve_coordinates(place_name: str) -> tuple[float, float]:
    geocoding_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={quote_plus(place_name)}&count=1&language=en&format=json"
    )
    payload = _safe_get_json(geocoding_url)
    if payload and payload.get("results"):
        first = payload["results"][0]
        return float(first["latitude"]), float(first["longitude"])
    return _fallback_coordinates_from_name(place_name)


def _normalize_articles(articles: list[dict], query_tag: str) -> list[dict]:
    normalized: list[dict] = []
    for article in articles:
        normalized.append(
            {
                "title": article.get("title", "Sin titulo"),
                "domain": article.get("domain", "N/A"),
                "url": article.get("url", ""),
                "seendate": article.get("seendate", ""),
                "query_tag": query_tag,
            }
        )
    return normalized


def check_weather_and_news(location: str, simulated_disaster: dict | None = None) -> dict:
    """Get online weather + news risk signals from free public endpoints."""
    geocoding_url = (
        "https://geocoding-api.open-meteo.com/v1/search?name="
        f"{quote_plus(location)}&count=1&language=en&format=json"
    )
    geocoding_payload = _safe_get_json(geocoding_url)
    if geocoding_payload and geocoding_payload.get("results"):
        result = geocoding_payload["results"][0]
        latitude = result["latitude"]
        longitude = result["longitude"]
        resolved_name = result["name"]
    else:
        # Fallback coordinates for Shanghai to keep demo resilient.
        latitude = 31.2304
        longitude = 121.4737
        resolved_name = location

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&current=wind_speed_10m,precipitation,weather_code"
    )
    weather_payload = _safe_get_json(weather_url)
    current_weather = (weather_payload or {}).get("current", {})
    wind_speed = float(current_weather.get("wind_speed_10m", 0.0))
    precipitation = float(current_weather.get("precipitation", 0.0))

    # Query strategy:
    # 1) local-port query
    # 2) region-aware hotspots (e.g., Strait of Hormuz, Bab el-Mandeb, Suez)
    local_query = (
        f'{location} port ("war" OR conflict OR sanctions OR blockade OR tariff OR strike OR attack)'
    )
    hotspot_query = (
        '("Strait of Hormuz" OR "Bab el-Mandeb" OR "Suez Canal" OR "Taiwan Strait" OR '
        '"Red Sea" OR sanctions OR conflict OR attack OR blockade) shipping'
    )
    local_articles = _fetch_gdelt_articles(local_query, max_records=8)
    hotspot_articles = _fetch_gdelt_articles(hotspot_query, max_records=8)
    geopolitical_articles = _normalize_articles(local_articles, "local_port") + _normalize_articles(
        hotspot_articles, "regional_hotspot"
    )

    # Deduplicate by URL/title to avoid repeated records.
    seen: set[str] = set()
    deduped_articles: list[dict] = []
    for article in geopolitical_articles:
        key = f'{article.get("url","")}|{article.get("title","")}'
        if key in seen:
            continue
        seen.add(key)
        deduped_articles.append(article)
    geopolitical_articles = deduped_articles[:8]

    top_headline = (
        geopolitical_articles[0]["title"]
        if geopolitical_articles
        else "No se encontraron titulares geopolíticos recientes; se usa riesgo meteorológico."
    )

    severity = _severity_from_signals(
        wind_speed_kmh=wind_speed,
        alert_hits=len(geopolitical_articles),
    )
    expected_delay_days = 1
    if severity == "medium":
        expected_delay_days = 3
    elif severity == "high":
        expected_delay_days = 5

    geopolitical_risk_score = min(100, len(geopolitical_articles) * 20 + int(wind_speed))

    simulated_event = None
    if simulated_disaster and simulated_disaster.get("enabled"):
        if simulated_disaster.get("region") in {"Global", "Middle East", "Red Sea", "Europe"}:
            simulated_event = simulated_disaster.get("event")
            geopolitical_risk_score = min(100, geopolitical_risk_score + int(simulated_disaster.get("risk_boost", 0)))
            if geopolitical_risk_score >= 70:
                severity = "high"
                expected_delay_days = max(expected_delay_days, 5)
            elif geopolitical_risk_score >= 45:
                severity = "medium"
                expected_delay_days = max(expected_delay_days, 3)

    return {
        "location": resolved_name,
        "alert_type": "weather_and_news_online",
        "severity": severity,
        "headline": top_headline,
        "expected_delay_days": expected_delay_days,
        "weather": {
            "wind_speed_kmh": wind_speed,
            "precipitation_mm": precipitation,
        },
        "news_signal_count": len(geopolitical_articles),
        "geopolitical_risk_score": geopolitical_risk_score,
        "geopolitical_articles": geopolitical_articles,
        "queries_used": {
            "local_query": local_query,
            "hotspot_query": hotspot_query,
        },
        "simulated_event": simulated_event,
        "source": {
            "weather_api": "open-meteo",
            "news_api": "gdelt",
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    }


def check_erp_inventory(product_id: str) -> dict:
    """Simulate an ERP stock check.

    Replace this with a real ERP connector (SAP/Oracle/NetSuite/etc).
    """
    return {
        "product_id": product_id,
        "stock_days_remaining": 5,
        "current_units": 1200,
        "average_daily_usage": 240,
        "risk_level": "critical",
    }


def calculate_alternative_routes(origin: str, destination: str, monitor_alert: dict) -> dict:
    """Build route options using online disruption signals from Agent 1.

    This keeps the PoC keyless and free while making Agent 3 data-driven.
    """
    severity = monitor_alert.get("severity", "low")
    base_delay = int(monitor_alert.get("expected_delay_days", 1))
    news_signal_count = int(monitor_alert.get("news_signal_count", 0))
    geopolitical_risk_score = int(monitor_alert.get("geopolitical_risk_score", 0))

    if severity == "high":
        risk_multiplier = 1.45
    elif severity == "medium":
        risk_multiplier = 1.20
    else:
        risk_multiplier = 1.0

    # Baseline values can be replaced by real freight connectors later.
    base_air_cost = 130000
    base_sea_cost = 55000

    dynamic_air_cost = int(base_air_cost * risk_multiplier + news_signal_count * 600 + geopolitical_risk_score * 120)
    dynamic_sea_cost = int(base_sea_cost * risk_multiplier + news_signal_count * 250 + geopolitical_risk_score * 65)

    air_eta = max(2, 2 + max(base_delay - 2, 0) + geopolitical_risk_score // 40)
    sea_eta = max(8, 8 + base_delay + geopolitical_risk_score // 25)

    origin_lat, origin_lon = _resolve_coordinates(origin)
    destination_lat, destination_lon = _resolve_coordinates(destination)

    route_map = {
        "origin_point": {"name": origin, "lat": origin_lat, "lon": origin_lon},
        "destination_point": {"name": destination, "lat": destination_lat, "lon": destination_lon},
        "paths": [
            {
                "route_id": "A",
                "route_name": "Opcion A - Flete Aereo",
                "color": [0, 160, 255],
                "path": [
                    [origin_lon, origin_lat],
                    [(origin_lon + destination_lon) / 2, (origin_lat + destination_lat) / 2 + 3.0],
                    [destination_lon, destination_lat],
                ],
            },
            {
                "route_id": "B",
                "route_name": "Opcion B - Desvio Maritimo",
                "color": [255, 140, 0],
                "path": [
                    [origin_lon, origin_lat],
                    [(origin_lon + destination_lon) / 2 - 4.0, (origin_lat + destination_lat) / 2 - 2.0],
                    [destination_lon, destination_lat],
                ],
            },
        ],
    }

    return {
        "origin": origin,
        "destination": destination,
        "online_context_used": {
            "severity": severity,
            "expected_delay_days": base_delay,
            "news_signal_count": news_signal_count,
            "geopolitical_risk_score": geopolitical_risk_score,
        },
        "route_map": route_map,
        "options": [
            {
                "id": "A",
                "name": "Flete Aereo",
                "eta_days": air_eta,
                "estimated_cost_usd": dynamic_air_cost,
                "service_level": "premium",
            },
            {
                "id": "B",
                "name": "Desvio Maritimo",
                "eta_days": sea_eta,
                "estimated_cost_usd": dynamic_sea_cost,
                "service_level": "economy",
            },
        ],
    }
