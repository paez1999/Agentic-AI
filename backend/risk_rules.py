"""
Deterministic simulation-aware risk escalation rules.

Applied AFTER the LLM scan to guarantee that physical proximity to an active
event is always reflected in the risk level — regardless of what the LLM said.

Rules
-----
Port risk
  • city in simulation.affected_cities          → at least HIGH
  • port within event radius_km                 → at least HIGH
  • port within event radius_km × 1.75          → at least MEDIUM

Route risk
  • route path intersects event impact zone     → HIGH (event LOW/MEDIUM)
                                                → CRITICAL (event HIGH/CRITICAL)
  • route endpoint in simulation.affected_cities → at least HIGH
"""
from __future__ import annotations

from backend.geo_utils import CITY_COORDS, city_within_radius, haversine_km
from backend.models import PortStatus, RiskLevel, RouteStatus
from backend.route_geometry import get_geometry
from backend.simulation import SimulationStore

_ORDER = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]


def _max(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    return a if _ORDER.index(a) >= _ORDER.index(b) else b


def apply_port_rules(status: PortStatus, sims: SimulationStore) -> PortStatus:
    floor = status.risk_level

    for ev in sims.list():
        # City-name match
        if status.city in ev.affected_cities:
            floor = _max(floor, RiskLevel.HIGH)

        # Coordinate-based proximity
        if ev.coordinates and ev.radius_km:
            lat, lon = ev.coordinates
            if city_within_radius(status.city, lat, lon, ev.radius_km):
                floor = _max(floor, RiskLevel.HIGH)
            elif city_within_radius(status.city, lat, lon, ev.radius_km * 1.75):
                floor = _max(floor, RiskLevel.MEDIUM)

    if floor == status.risk_level:
        return status
    return status.model_copy(update={"risk_level": floor})


def _geometry_intersects(
    origin: str,
    destination: str,
    route_type: str,
    event_lat: float,
    event_lon: float,
    radius_km: float,
) -> bool:
    """
    Check whether the *actual* route geometry (shipping lanes, road paths,
    great-circle arcs) passes within radius_km of the event location.
    """
    waypoints = get_geometry(origin, destination, route_type)
    for lon, lat in waypoints:
        if haversine_km(lat, lon, event_lat, event_lon) <= radius_km:
            return True
    return False


def _point_in_polygon(lon: float, lat: float, polygon: list[list[float]]) -> bool:
    """Ray-casting point-in-polygon test. polygon is [[lon, lat], ...]."""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i][0], polygon[i][1]
        xj, yj = polygon[j][0], polygon[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def _geometry_intersects_polygon(
    origin: str,
    destination: str,
    route_type: str,
    polygon: list[list[float]],
) -> bool:
    """Check whether any waypoint of the route falls inside the given polygon."""
    waypoints = get_geometry(origin, destination, route_type)
    for lon, lat in waypoints:
        if _point_in_polygon(lon, lat, polygon):
            return True
    return False


def apply_route_rules(
    status: RouteStatus,
    sims: SimulationStore,
    extra_coords: dict[str, tuple[float, float]] | None = None,
) -> RouteStatus:
    floor = status.risk_level

    for ev in sims.list():
        # Endpoint city name match → at least HIGH
        if ev.affected_cities and (
            status.origin.lower() in [c.lower() for c in ev.affected_cities]
            or status.destination.lower() in [c.lower() for c in ev.affected_cities]
        ):
            floor = _max(floor, RiskLevel.HIGH)

        # Coordinate-based intersection using real route geometry
        if ev.coordinates and ev.radius_km:
            lat, lon = ev.coordinates
            if _geometry_intersects(
                status.origin, status.destination,
                status.route_type, lat, lon, ev.radius_km,
            ):
                if ev.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                    floor = _max(floor, RiskLevel.CRITICAL)
                else:
                    floor = _max(floor, RiskLevel.HIGH)

        # Polygon-based intersection (hurricane zones and other area events)
        if ev.polygon and len(ev.polygon) >= 3:
            if _geometry_intersects_polygon(
                status.origin, status.destination,
                status.route_type, ev.polygon,
            ):
                if ev.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                    floor = _max(floor, RiskLevel.CRITICAL)
                else:
                    floor = _max(floor, RiskLevel.HIGH)

    if floor == status.risk_level:
        return status
    return status.model_copy(update={"risk_level": floor})
