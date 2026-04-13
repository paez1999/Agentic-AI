from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Coroutine, Any

if TYPE_CHECKING:
    pass


class AutoScanScheduler:
    def __init__(
        self,
        scan_all_fn: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        self._scan_all = scan_all_fn
        self._enabled: bool = False
        self._interval_minutes: int = 15
        self._task: asyncio.Task | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def interval_minutes(self) -> int:
        return self._interval_minutes

    def configure(self, enabled: bool, interval_minutes: int) -> None:
        self._enabled = enabled
        self._interval_minutes = max(1, interval_minutes)
        if self._task and not self._task.done():
            self._task.cancel()
        if self._enabled:
            self._task = asyncio.create_task(self._loop())

    async def _loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._interval_minutes * 60)
                if self._enabled:
                    await self._scan_all()
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
