from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.models import PortStatus, RiskLevel

_DATA_FILE = Path(__file__).parent / "data" / "ports.json"


class PortRegistry:
    def __init__(self) -> None:
        self._ports: list[str] = []
        self._statuses: dict[str, PortStatus] = {}
        self._lock = threading.Lock()
        self._load()

    # ── persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        if _DATA_FILE.exists():
            try:
                data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
                self._ports = data.get("ports", [])
                for city, raw in data.get("statuses", {}).items():
                    try:
                        self._statuses[city] = PortStatus.model_validate(raw)
                    except Exception:
                        self._statuses[city] = PortStatus(city=city)
            except Exception:
                self._ports = []
                self._statuses = {}

    def _save(self) -> None:
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "ports": self._ports,
            "statuses": {
                city: s.model_dump(mode="json")
                for city, s in self._statuses.items()
            },
        }
        payload = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        with self._lock:
            _DATA_FILE.write_text(payload, encoding="utf-8")

    # ── public API ────────────────────────────────────────────────────────────

    def list_ports(self) -> list[PortStatus]:
        return [
            self._statuses.get(city, PortStatus(city=city))
            for city in self._ports
        ]

    def has_port(self, city: str) -> bool:
        return city in self._ports

    def add_port(self, city: str) -> bool:
        """Returns True if newly added, False if already present."""
        if city in self._ports:
            return False
        self._ports.append(city)
        if city not in self._statuses:
            self._statuses[city] = PortStatus(city=city)
        self._save()
        return True

    def remove_port(self, city: str) -> bool:
        """Returns True if removed, False if not found."""
        if city not in self._ports:
            return False
        self._ports.remove(city)
        self._statuses.pop(city, None)
        self._save()
        return True

    def update_status(self, city: str, status: PortStatus) -> None:
        self._statuses[city] = status
        self._save()

    def get_status(self, city: str) -> PortStatus | None:
        if city not in self._ports:
            return None
        return self._statuses.get(city, PortStatus(city=city))
