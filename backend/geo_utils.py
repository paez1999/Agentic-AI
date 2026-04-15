"""Geospatial utilities for coordinate-based simulation impact detection."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Known city coordinates [lon, lat] — mirrors src/tools/routing.py COORDS
CITY_COORDS: dict[str, tuple[float, float]] = {
    "veracruz":       (-96.1342, 19.1738),
    "houston":        (-95.3698, 29.7604),
    "tampa":          (-82.4572, 27.9506),
    "mexico city":    (-99.1332, 19.4326),
    "panama":         (-79.5197,  8.9936),
    "miami":          (-80.1918, 25.7617),
    "guatemala":      (-90.5069, 14.6349),
    "guatemala city": (-90.5069, 14.6349),
    "new orleans":    (-90.0715, 29.9511),
    "los angeles":    (-118.2437, 34.0522),
    "new york":       (-74.0060, 40.7128),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _interpolate_gc(
    lon1: float, lat1: float,
    lon2: float, lat2: float,
    steps: int = 20,
) -> list[tuple[float, float]]:
    """
    Return `steps` evenly-spaced (lon, lat) points along the great-circle
    between two endpoints (inclusive).
    """
    points: list[tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        lat = lat1 + t * (lat2 - lat1)
        lon = lon1 + t * (lon2 - lon1)
        points.append((lon, lat))
    return points


def _city_lonlat(city: str) -> tuple[float, float] | None:
    """Look up (lon, lat) for a city name (case-insensitive)."""
    return CITY_COORDS.get(city.lower().strip())


def city_within_radius(city: str, event_lat: float, event_lon: float, radius_km: float) -> bool:
    """Return True if a city centre is within radius_km of the event point."""
    coords = _city_lonlat(city)
    if coords is None:
        return False
    lon, lat = coords
    return haversine_km(lat, lon, event_lat, event_lon) <= radius_km


def route_intersects_radius(
    origin: str,
    destination: str,
    event_lat: float,
    event_lon: float,
    radius_km: float,
    steps: int = 30,
    extra_coords: dict[str, tuple[float, float]] | None = None,
) -> bool:
    """
    Return True if any interpolated point along the origin→destination
    great-circle path lies within `radius_km` of the event location.

    `extra_coords` can supply additional city → (lon, lat) pairs beyond
    the hardcoded CITY_COORDS dict (e.g. dynamically added ports).
    """
    def _lookup(city: str) -> tuple[float, float] | None:
        c = _city_lonlat(city)
        if c:
            return c
        if extra_coords:
            return extra_coords.get(city.lower().strip())
        return None

    o_coords = _lookup(origin)
    d_coords = _lookup(destination)
    if o_coords is None or d_coords is None:
        return False
    o_lon, o_lat = o_coords
    d_lon, d_lat = d_coords
    for lon, lat in _interpolate_gc(o_lon, o_lat, d_lon, d_lat, steps):
        if haversine_km(lat, lon, event_lat, event_lon) <= radius_km:
            return True
    return False


def find_affected_cities(
    all_cities: list[str],
    event_lat: float,
    event_lon: float,
    radius_km: float,
) -> list[str]:
    """Return cities whose centre is within radius_km of the event point."""
    return [c for c in all_cities if city_within_radius(c, event_lat, event_lon, radius_km)]


def find_affected_routes(
    routes: list[tuple[str, str, str]],  # (route_id, origin, destination)
    event_lat: float,
    event_lon: float,
    radius_km: float,
) -> list[str]:
    """Return route_ids whose path passes within radius_km of the event point."""
    return [
        route_id
        for route_id, origin, destination in routes
        if route_intersects_radius(origin, destination, event_lat, event_lon, radius_km)
    ]
