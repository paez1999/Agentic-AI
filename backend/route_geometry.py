"""
Compute display geometry (list of [lon, lat] waypoints) for a route.

- maritime:    predefined shipping-lane waypoints that hug coasts / avoid land
- terrestrial: OpenRouteService driving-car geometry (falls back to straight line)
- air:         great-circle interpolation (100 pts → curves on Mercator projection)
"""
from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from urllib.parse import quote_plus
from urllib.request import urlopen

import httpx

# ── Known city coordinates [lon, lat] ─────────────────────────────────────────
CITY_COORDS: dict[str, list[float]] = {
    "veracruz":       [-96.1342, 19.1738],
    "houston":        [-95.3698, 29.7604],
    "tampa":          [-82.4572, 27.9506],
    "mexico city":    [-99.1332, 19.4326],
    "panama":         [-79.5197,  8.9936],
    "miami":          [-80.1918, 25.7617],
    "guatemala":      [-90.5069, 14.6349],
    "guatemala city": [-90.5069, 14.6349],
    "new orleans":    [-90.0715, 29.9511],
    "los angeles":    [-118.2437, 34.0522],
    "new york":       [-74.0060, 40.7128],
}

# ── Geocoding fallback (cached per city name) ─────────────────────────────────
@lru_cache(maxsize=256)
def _geocode(city: str) -> list[float] | None:
    """Return [lon, lat] for any city via Open-Meteo geocoding (free, no key)."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote_plus(city)}&count=1&language=en&format=json"
        with urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        results = data.get("results") or []
        if results:
            return [float(results[0]["longitude"]), float(results[0]["latitude"])]
    except Exception:
        pass
    return None


def _resolve_coord(city: str) -> list[float] | None:
    """Look up [lon, lat] — CITY_COORDS first, geocoding fallback."""
    key = city.lower().strip()
    return CITY_COORDS.get(key) or _geocode(key)


# ── Maritime shipping-lane waypoints [lon, lat] ────────────────────────────────
# Key: frozenset of two lowercase city names (order-independent)
_MARITIME: dict[frozenset, list[list[float]]] = {
    frozenset({"houston", "veracruz"}): [
        [-95.3698, 29.7604],   # Houston (Galveston exit)
        [-94.8,   28.5 ],      # Gulf – SW
        [-94.0,   26.0 ],      # Open Gulf
        [-93.5,   23.5 ],      # Deep Gulf
        [-95.0,   21.5 ],      # Approaching Veracruz
        [-96.1342, 19.1738],   # Veracruz
    ],
    frozenset({"houston", "tampa"}): [
        [-95.3698, 29.7604],
        [-91.5,   28.5 ],      # Mississippi Delta offshore
        [-88.0,   27.0 ],      # Central Gulf
        [-85.0,   27.0 ],
        [-83.0,   27.5 ],
        [-82.4572, 27.9506],   # Tampa
    ],
    frozenset({"houston", "panama"}): [
        [-95.3698, 29.7604],
        [-93.0,   25.5 ],      # Gulf south
        [-88.5,   21.5 ],      # Yucatan Channel north
        [-86.5,   19.5 ],      # Yucatan Channel
        [-84.0,   16.5 ],      # Caribbean NW
        [-81.5,   12.5 ],      # Caribbean central
        [-80.0,   10.0 ],
        [-79.5197,  8.9936],   # Panama (Colón)
    ],
    frozenset({"veracruz", "tampa"}): [
        [-96.1342, 19.1738],
        [-93.5,   21.5 ],      # Gulf SE
        [-89.0,   21.5 ],      # Yucatan Channel south
        [-86.0,   22.5 ],      # North of Yucatan
        [-83.5,   24.0 ],      # Cuba north coast offset
        [-82.0,   26.0 ],      # Florida Strait approach
        [-82.4572, 27.9506],
    ],
    frozenset({"veracruz", "panama"}): [
        [-96.1342, 19.1738],
        [-91.0,   18.5 ],      # Yucatan Channel S approach
        [-87.5,   16.0 ],      # Caribbean W
        [-84.0,   13.5 ],      # Caribbean central
        [-81.0,   10.5 ],
        [-79.5197,  8.9936],
    ],
    frozenset({"tampa", "panama"}): [
        [-82.4572, 27.9506],
        [-81.0,   25.0 ],      # Florida Strait
        [-80.0,   22.5 ],      # Cuba S
        [-79.5,   18.0 ],      # Caribbean
        [-79.5,   13.5 ],
        [-79.5197,  8.9936],
    ],
    frozenset({"miami", "panama"}): [
        [-80.1918, 25.7617],
        [-79.8,   23.5 ],      # Cuba north pass
        [-79.5,   20.0 ],      # Cuba east
        [-79.0,   17.0 ],      # Caribbean W
        [-79.5,   13.5 ],
        [-79.5197,  8.9936],
    ],
    frozenset({"miami", "houston"}): [
        [-80.1918, 25.7617],
        [-82.0,   26.5 ],      # Florida west coast
        [-84.0,   27.5 ],      # Gulf entry
        [-87.0,   27.5 ],      # Central Gulf
        [-90.5,   28.0 ],
        [-93.0,   28.5 ],
        [-95.3698, 29.7604],
    ],
    frozenset({"miami", "veracruz"}): [
        [-80.1918, 25.7617],
        [-82.5,   25.0 ],
        [-84.5,   24.0 ],      # Cuba south
        [-87.5,   22.0 ],      # Yucatan Strait
        [-90.0,   21.0 ],
        [-92.5,   20.0 ],
        [-96.1342, 19.1738],
    ],
}

# ── Terrestrial road checkpoints (used only if ORS unavailable) ───────────────
_TERRESTRIAL_FALLBACK: dict[frozenset, list[list[float]]] = {
    frozenset({"houston", "mexico city"}): [
        [-95.3698, 29.7604],
        [-99.5,   27.5 ],   # Laredo area
        [-99.8,   25.7 ],   # Monterrey
        [-100.3,  22.5 ],   # San Luis Potosí area
        [-99.1332, 19.4326],
    ],
    frozenset({"veracruz", "mexico city"}): [
        [-96.1342, 19.1738],
        [-97.0,   19.0 ],   # Orizaba pass
        [-98.4,   19.1 ],   # Puebla
        [-99.1332, 19.4326],
    ],
    frozenset({"houston", "veracruz"}): [
        [-95.3698, 29.7604],
        [-99.5,   27.5 ],
        [-99.8,   25.7 ],   # Monterrey
        [-98.0,   22.0 ],
        [-97.5,   20.5 ],
        [-96.1342, 19.1738],
    ],
    # Panama ↔ Guatemala via Pan-American Hwy
    frozenset({"panama", "guatemala"}): [
        [-79.5197,  8.9936],
        [-83.8,   10.0 ],   # Costa Rica
        [-85.2,   11.0 ],   # Managua
        [-86.3,   12.1 ],   # Nicaragua north
        [-86.9,   13.0 ],   # Honduras
        [-87.2,   14.1 ],   # El Salvador
        [-90.5069, 14.6349], # Guatemala City
    ],
    frozenset({"panama", "guatemala city"}): [
        [-79.5197,  8.9936],
        [-83.8,   10.0 ],
        [-85.2,   11.0 ],
        [-86.3,   12.1 ],
        [-86.9,   13.0 ],
        [-87.2,   14.1 ],
        [-90.5069, 14.6349],
    ],
    frozenset({"mexico city", "panama"}): [
        [-99.1332, 19.4326],
        [-96.5,   17.0 ],   # Oaxaca region
        [-91.5,   15.5 ],   # Guatemala border
        [-88.0,   15.7 ],   # Guatemala City
        [-87.2,   14.1 ],   # El Salvador
        [-86.9,   13.0 ],   # Honduras
        [-86.3,   12.1 ],   # Nicaragua north
        [-85.2,   11.0 ],   # Managua
        [-83.8,   10.0 ],   # Costa Rica
        [-79.5197,  8.9936],
    ],
    # Houston ↔ Tampa via I-10 coastal highway
    frozenset({"houston", "tampa"}): [
        [-95.3698, 29.7604],
        [-93.8,   30.2 ],   # Beaumont / Orange TX
        [-91.2,   30.4 ],   # Baton Rouge
        [-90.0,   29.9 ],   # New Orleans
        [-88.0,   30.5 ],   # Biloxi / Gulfport
        [-86.3,   30.7 ],   # Pensacola
        [-84.3,   30.4 ],   # Tallahassee area
        [-83.0,   29.7 ],   # Gainesville area
        [-82.4572, 27.9506], # Tampa
    ],
    # Houston ↔ Panama via Mexico + Central America (Pan-American Hwy)
    frozenset({"houston", "panama"}): [
        [-95.3698, 29.7604],
        [-99.5,   27.5 ],   # Laredo
        [-99.8,   25.7 ],   # Monterrey
        [-100.3,  22.5 ],   # San Luis Potosí
        [-99.1332, 19.4326], # Mexico City
        [-96.5,   17.0 ],   # Oaxaca
        [-91.5,   15.5 ],   # Guatemala border
        [-88.0,   15.7 ],   # Guatemala City
        [-87.2,   14.1 ],   # El Salvador
        [-86.9,   13.0 ],   # Honduras
        [-85.2,   11.0 ],   # Managua
        [-83.8,   10.0 ],   # Costa Rica
        [-79.5197,  8.9936],
    ],
    # Veracruz ↔ Tampa via Yucatan overland + US gulf coast
    frozenset({"veracruz", "tampa"}): [
        [-96.1342, 19.1738],
        [-94.0,   18.0 ],   # Villahermosa
        [-90.5,   18.0 ],   # Campeche
        [-89.6,   21.0 ],   # Merida / Yucatan
        [-88.3,   21.5 ],   # Cancun area (overland)
        [-87.5,   23.2 ],   # Chetumal border
        [-86.7,   25.5 ],   # Crossing into Belize / Yucatan ferry point
        [-84.5,   28.0 ],   # Florida – inland
        [-82.4572, 27.9506],
    ],
    # Veracruz ↔ Panama via Pan-American Hwy south
    frozenset({"veracruz", "panama"}): [
        [-96.1342, 19.1738],
        [-97.0,   19.0 ],   # Orizaba
        [-98.4,   19.1 ],   # Puebla
        [-99.1332, 19.4326], # Mexico City
        [-96.5,   17.0 ],   # Oaxaca
        [-91.5,   15.5 ],   # Guatemala border
        [-88.0,   15.7 ],   # Guatemala City
        [-87.2,   14.1 ],   # El Salvador
        [-86.9,   13.0 ],   # Honduras
        [-85.2,   11.0 ],   # Managua
        [-83.8,   10.0 ],   # Costa Rica
        [-79.5197,  8.9936],
    ],
    # Tampa ↔ Panama via Florida, Cuba border, then Central America
    frozenset({"tampa", "panama"}): [
        [-82.4572, 27.9506],
        [-81.7,   26.0 ],   # Fort Myers / Naples FL
        [-80.2,   25.8 ],   # Miami
        [-80.5,   24.5 ],   # Florida Keys
        [-83.0,   23.0 ],   # Cuba south coast bypass (overland border not possible – ferry/cross)
        [-85.5,   20.5 ],   # Yucatan west coast
        [-88.0,   15.7 ],   # Guatemala City
        [-87.2,   14.1 ],   # El Salvador
        [-86.9,   13.0 ],   # Honduras
        [-85.2,   11.0 ],   # Managua
        [-83.8,   10.0 ],   # Costa Rica
        [-79.5197,  8.9936],
    ],
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _densify(waypoints: list[list[float]], steps: int = 20) -> list[list[float]]:
    """
    Insert `steps` linearly-interpolated points between every consecutive
    waypoint pair.  Turns sparse 6-point maritime lanes into 100+ point paths
    so that events between waypoints are still detected by haversine checks.
    """
    if len(waypoints) < 2:
        return waypoints
    result: list[list[float]] = []
    for i in range(len(waypoints) - 1):
        lon1, lat1 = waypoints[i]
        lon2, lat2 = waypoints[i + 1]
        for j in range(steps):
            t = j / steps
            result.append([lon1 + t * (lon2 - lon1), lat1 + t * (lat2 - lat1)])
    result.append(waypoints[-1])
    return result


def _great_circle(
    lon1: float, lat1: float,
    lon2: float, lat2: float,
    n: int = 80,
) -> list[list[float]]:
    """Return n+1 [lon, lat] points along the great-circle path."""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append([lon1 + t * (lon2 - lon1), lat1 + t * (lat2 - lat1)])
    return pts


def _ors_geometry(origin: str, destination: str) -> list[list[float]] | None:
    """Call ORS driving-car for actual road geometry. Returns None on failure."""
    api_key = os.environ.get("ORS_API_KEY", "")
    if not api_key:
        return None
    o = _resolve_coord(origin)
    d = _resolve_coord(destination)
    if not o or not d:
        return None
    try:
        resp = httpx.post(
            "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
            json={"coordinates": [o, d]},
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        coords = resp.json()["features"][0]["geometry"]["coordinates"]
        return coords  # already [lon, lat]
    except Exception:
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def get_geometry(
    origin: str,
    destination: str,
    route_type: str,
) -> list[list[float]]:
    """
    Return display geometry as a list of [lon, lat] pairs.
    Delegates to route_planner for maritime/air; uses ORS + fallbacks for terrestrial.
    """
    from backend import route_planner as _planner
    result = _planner.plan(origin, destination, mode=route_type or "maritime")
    wps = result.get("waypoints", [])
    if wps:
        return wps

    # Last-resort: two-point endpoint line
    o_coord = _resolve_coord(origin.lower().strip())
    d_coord = _resolve_coord(destination.lower().strip())
    if o_coord and d_coord:
        return [o_coord, d_coord]
    return []
