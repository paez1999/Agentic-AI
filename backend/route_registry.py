from __future__ import annotations

import json
import threading
from pathlib import Path

from backend.models import RouteStatus, RiskLevel

_DATA_FILE = Path(__file__).parent / "data" / "routes.json"


class RouteRegistry:
    def __init__(self) -> None:
        self._routes: list[str] = []
        self._statuses: dict[str, RouteStatus] = {}
        self._lock = threading.Lock()
        self._load()

    # ── persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        if _DATA_FILE.exists():
            try:
                data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
                self._routes = data.get("routes", [])
                for route_id, raw in data.get("statuses", {}).items():
                    try:
                        self._statuses[route_id] = RouteStatus.model_validate(raw)
                    except Exception:
                        origin, destination = _split_route_id(route_id)
                        self._statuses[route_id] = RouteStatus(
                            route_id=route_id, origin=origin, destination=destination
                        )
                # Ensure every route in the list has a status entry
                for route_id in self._routes:
                    if route_id not in self._statuses:
                        origin, destination = _split_route_id(route_id)
                        self._statuses[route_id] = RouteStatus(
                            route_id=route_id, origin=origin, destination=destination
                        )
            except Exception:
                self._routes = []
                self._statuses = {}

    def _save(self) -> None:
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "routes": self._routes,
            "statuses": {
                route_id: s.model_dump(mode="json")
                for route_id, s in self._statuses.items()
            },
        }
        payload = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        with self._lock:
            _DATA_FILE.write_text(payload, encoding="utf-8")

    # ── public API ────────────────────────────────────────────────────────────

    def list_routes(self) -> list[RouteStatus]:
        return [
            self._statuses.get(
                route_id,
                RouteStatus(route_id=route_id, **(lambda o, d: {"origin": o, "destination": d})(*_split_route_id(route_id))),
            )
            for route_id in self._routes
        ]

    def has_route(self, route_id: str) -> bool:
        return route_id in self._routes

    def add_route(self, origin: str, destination: str, route_type: str = "maritime") -> RouteStatus | None:
        """Returns None if already exists, else creates a fresh RouteStatus and saves."""
        route_id = _make_route_id(origin, destination)
        if route_id in self._routes:
            return None
        self._routes.append(route_id)
        status = RouteStatus(route_id=route_id, origin=origin, destination=destination, route_type=route_type)
        self._statuses[route_id] = status
        self._save()
        return status

    def remove_route(self, route_id: str) -> bool:
        """Returns True if removed, False if not found."""
        if route_id not in self._routes:
            return False
        self._routes.remove(route_id)
        self._statuses.pop(route_id, None)
        self._save()
        return True

    def update_status(self, route_id: str, status: RouteStatus) -> None:
        self._statuses[route_id] = status
        self._save()

    def get_status(self, route_id: str) -> RouteStatus | None:
        if route_id not in self._routes:
            return None
        return self._statuses.get(
            route_id,
            RouteStatus(route_id=route_id, **(lambda o, d: {"origin": o, "destination": d})(*_split_route_id(route_id))),
        )


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_route_id(origin: str, destination: str) -> str:
    return f"{origin.lower().replace(' ', '-')}-to-{destination.lower().replace(' ', '-')}"


def _split_route_id(route_id: str) -> tuple[str, str]:
    """Reconstruct origin and destination from a route_id like 'foo-bar-to-baz-qux'."""
    if "-to-" in route_id:
        parts = route_id.split("-to-", 1)
        origin = parts[0].replace("-", " ").title()
        destination = parts[1].replace("-", " ").title()
    else:
        origin = route_id.title()
        destination = "Unknown"
    return origin, destination
