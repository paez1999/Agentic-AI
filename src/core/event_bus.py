"""NATS event bus with CloudEvents envelope.

Publishes domain events from the supply-chain orchestrator to NATS subjects.
Uses a background asyncio thread so the synchronous agent loop can publish
without blocking.

Subjects:
    supply_chain.risk.alert         — after Phase 1 (RiskMonitor)
    supply_chain.inventory.updated  — after Phase 2 (InventoryManager)
    supply_chain.action.executed    — after Phase 3 (RouteOptimizer)

Usage:
    bus = EventBus()                         # connects; falls back if unreachable
    bus.publish("supply_chain.risk.alert", "com.supplychain.risk.alert", data)
    bus.close()

Graceful fallback: if NATS is not reachable at startup, EventBus enters
no-op mode — all publish calls are silently dropped so the pipeline still runs.
"""

import asyncio
import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Callable


_SOURCE = "supply-chain/orchestrator"


class EventBus:
    """Sync-friendly NATS publisher + subscriber backed by a daemon asyncio thread."""

    def __init__(self, url: str = "nats://localhost:4222"):
        self._url = url
        self._nc = None          # nats.aio.client.Client
        self._enabled = False    # False if NATS unreachable

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        ready = threading.Event()
        asyncio.run_coroutine_threadsafe(self._connect(ready), self._loop)
        ready.wait(timeout=5)    # short timeout — NATS is optional

    async def _connect(self, ready: threading.Event) -> None:
        try:
            import nats  # nats-py
            async def _err_cb(exc):
                pass  # suppress nats-py internal error noise

            self._nc = await asyncio.wait_for(
                nats.connect(self._url, error_cb=_err_cb), timeout=4.0
            )
            self._enabled = True
            print(f"[EventBus] Connected to NATS at {self._url}")
        except Exception as exc:
            print(f"[EventBus] NATS not reachable ({type(exc).__name__}) — no-op mode")
        finally:
            ready.set()

    # ------------------------------------------------------------------
    # CloudEvents envelope
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap(event_type: str, data: dict) -> bytes:
        """Wrap data in a CloudEvents 1.0 JSON envelope."""
        envelope = {
            "specversion": "1.0",
            "id": str(uuid.uuid4()),
            "source": _SOURCE,
            "type": event_type,
            "datacontenttype": "application/json",
            "time": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        return json.dumps(envelope, ensure_ascii=False).encode()

    # ------------------------------------------------------------------
    # Publish
    # ------------------------------------------------------------------

    def publish(self, subject: str, event_type: str, data: dict) -> None:
        """Publish a CloudEvent to a NATS subject (fire-and-forget, sync)."""
        if not self._enabled:
            return
        payload = self._wrap(event_type, data)
        asyncio.run_coroutine_threadsafe(
            self._nc.publish(subject, payload), self._loop
        )

    # ------------------------------------------------------------------
    # Subscribe
    # ------------------------------------------------------------------

    def subscribe(self, subject: str, callback: Callable[[str, dict], None]) -> None:
        """Subscribe to a NATS subject.

        callback(subject, data) is called in the background thread for each message.
        data is the CloudEvents envelope as a dict.
        """
        if not self._enabled:
            return

        async def _handler(msg):
            try:
                envelope = json.loads(msg.data.decode())
                callback(msg.subject, envelope)
            except Exception as exc:
                print(f"[EventBus] Handler error on {msg.subject}: {exc}")

        asyncio.run_coroutine_threadsafe(
            self._nc.subscribe(subject, cb=_handler), self._loop
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        if self._enabled and self._nc is not None:
            try:
                asyncio.run_coroutine_threadsafe(
                    self._nc.drain(), self._loop
                ).result(timeout=5)
            except Exception:
                pass
        self._loop.call_soon_threadsafe(self._loop.stop)

    @property
    def enabled(self) -> bool:
        return self._enabled
