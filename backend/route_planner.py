from __future__ import annotations

import heapq
import json
import logging
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.geo_utils import slerp_gc, _geocode

logger = logging.getLogger(__name__)

_GRAPH_PATH = Path(__file__).parent / "data" / "maritime_graph.json"


def _haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371.0
    lat1r, lon1r, lat2r, lon2r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def _point_in_bbox(lon: float, lat: float, bbox: dict) -> bool:
    return (bbox["lon_min"] <= lon <= bbox["lon_max"] and
            bbox["lat_min"] <= lat <= bbox["lat_max"])


def _edge_crosses_bbox(waypoints: list, bbox: dict) -> bool:
    return any(_point_in_bbox(p[0], p[1], bbox) for p in waypoints)


class MaritimeGraph:
    def __init__(self) -> None:
        data = json.loads(_GRAPH_PATH.read_text(encoding="utf-8"))
        self._nodes: dict[str, dict] = {n["id"]: n for n in data["nodes"]}
        self._chokepoint_regions: dict[str, dict] = data["chokepoint_regions"]
        self._adj: dict[str, list[tuple[str, dict]]] = {n: [] for n in self._nodes}
        for edge in data["edges"]:
            f, t = edge["from"], edge["to"]
            self._adj.setdefault(f, []).append((t, edge))
            self._adj.setdefault(t, []).append((f, {**edge, "waypoints": list(reversed(edge["waypoints"]))}))

    def snap_to_nearest(self, lon: float, lat: float, max_km: float = 200.0) -> str | None:
        best_id, best_dist = None, float("inf")
        for nid, n in self._nodes.items():
            d = _haversine(lon, lat, n["lon"], n["lat"])
            if d < best_dist:
                best_dist = d
                best_id = nid
        if best_dist > max_km:
            logger.warning("Nearest node %.0f km away (>%.0f km limit) — refusing maritime snap", best_dist, max_km)
            return None
        return best_id

    def _resolve_avoid_bboxes(self, avoid: list) -> list[dict]:
        bboxes: list[dict] = []
        for item in avoid:
            if isinstance(item, str):
                bbox = self._chokepoint_regions.get(item)
                if bbox:
                    bboxes.append(bbox)
            elif isinstance(item, dict):
                if "bbox" in item:
                    bboxes.append(item["bbox"])
                elif "circle" in item:
                    lon, lat, r_km = item["circle"]
                    deg = r_km / 111.0
                    bboxes.append({"lon_min": lon - deg, "lon_max": lon + deg,
                                   "lat_min": lat - deg, "lat_max": lat + deg})
        return bboxes

    def plan(self, origin_id: str, dest_id: str, avoid: list = []) -> dict:
        if origin_id not in self._nodes or dest_id not in self._nodes:
            return {"waypoints": [], "chokepoints_crossed": [], "distance_km": 0, "avoid_applied": avoid}

        avoid_bboxes = self._resolve_avoid_bboxes(avoid)
        dist: dict[str, float] = {n: float("inf") for n in self._nodes}
        prev: dict[str, tuple[str, dict] | None] = {n: None for n in self._nodes}
        dist[origin_id] = 0.0
        pq: list[tuple[float, str]] = [(0.0, origin_id)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            if u == dest_id:
                break
            for v, edge in self._adj.get(u, []):
                wps = edge["waypoints"]
                if avoid_bboxes and any(_edge_crosses_bbox(wps, bbox) for bbox in avoid_bboxes):
                    continue
                nd = d + edge["distance_km"]
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = (u, edge)
                    heapq.heappush(pq, (nd, v))

        if dist[dest_id] == float("inf"):
            logger.warning("No maritime path %s→%s with avoid=%s", origin_id, dest_id, avoid)
            return {"waypoints": [], "chokepoints_crossed": [], "distance_km": 0, "avoid_applied": avoid}

        path_edges: list[tuple[str, str, dict]] = []
        cur = dest_id
        while prev[cur] is not None:
            u, edge = prev[cur]
            path_edges.append((u, cur, edge))
            cur = u
        path_edges.reverse()

        waypoints: list[list[float]] = []
        chokepoints: list[str] = []
        for u, v, edge in path_edges:
            wps = edge["waypoints"]
            waypoints.extend(wps if not waypoints else wps[1:])
            for cp_name, bbox in self._chokepoint_regions.items():
                if cp_name not in chokepoints and any(_point_in_bbox(p[0], p[1], bbox) for p in wps):
                    chokepoints.append(cp_name)

        return {
            "waypoints": waypoints,
            "chokepoints_crossed": chokepoints,
            "distance_km": round(dist[dest_id]),
            "avoid_applied": avoid,
        }


_graph: MaritimeGraph | None = None


def _get_graph() -> MaritimeGraph:
    global _graph
    if _graph is None:
        _graph = MaritimeGraph()
    return _graph


def _slerp_fallback(origin: str, destination: str) -> dict:
    try:
        o = _geocode(origin)
        d = _geocode(destination)
        if o and d:
            wps = slerp_gc(o[0], o[1], d[0], d[1])
            dist = _haversine(o[0], o[1], d[0], d[1])
            return {"waypoints": wps, "chokepoints_crossed": [], "distance_km": round(dist), "avoid_applied": []}
    except Exception as e:
        logger.warning("slerp fallback failed: %s", e)
    return {"waypoints": [], "chokepoints_crossed": [], "distance_km": 0, "avoid_applied": []}


def plan(origin: str, destination: str, mode: str = "maritime", avoid: list = []) -> dict:
    """Plan a route. mode: 'maritime' | 'air' | 'terrestrial'."""
    if mode == "air":
        return _slerp_fallback(origin, destination)

    if mode == "maritime":
        try:
            g = _get_graph()
            o = _geocode(origin)
            d = _geocode(destination)
            if o and d:
                origin_id = g.snap_to_nearest(o[0], o[1])
                dest_id = g.snap_to_nearest(d[0], d[1])
                if origin_id and dest_id:
                    result = g.plan(origin_id, dest_id, avoid)
                    if result["waypoints"]:
                        return result
        except Exception as e:
            logger.warning("Maritime plan error: %s", e)
        return _slerp_fallback(origin, destination)

    # Terrestrial — try ORS, fall back to slerp
    ors_key = os.getenv("ORS_API_KEY", "")
    if ors_key:
        try:
            import requests
            o = _geocode(origin)
            d = _geocode(destination)
            if o and d:
                resp = requests.post(
                    "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
                    headers={"Authorization": ors_key, "Content-Type": "application/json"},
                    json={"coordinates": [[o[0], o[1]], [d[0], d[1]]]},
                    timeout=10,
                )
                if resp.status_code == 200:
                    feature = resp.json()["features"][0]
                    coords = feature["geometry"]["coordinates"]
                    dist = feature["properties"]["segments"][0]["distance"] / 1000
                    return {"waypoints": coords, "chokepoints_crossed": [], "distance_km": round(dist), "avoid_applied": []}
        except Exception as e:
            logger.warning("ORS terrestrial error: %s", e)
    return _slerp_fallback(origin, destination)
