import threading
from typing import Callable, Optional


class RefreshScheduler:
    """Auto-refresh timer using threading.Timer (fires callback on background thread)."""

    def __init__(self, callback: Callable, interval_minutes: int = 0):
        self._callback = callback
        self._interval = interval_minutes
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._interval > 0:
            self._schedule_next()

    def stop(self) -> None:
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None

    def set_interval(self, minutes: int) -> None:
        self.stop()
        self._interval = minutes
        if minutes > 0:
            self._schedule_next()

    def _schedule_next(self) -> None:
        with self._lock:
            self._timer = threading.Timer(
                self._interval * 60, self._tick
            )
            self._timer.daemon = True
            self._timer.start()

    def _tick(self) -> None:
        try:
            self._callback()
        finally:
            if self._interval > 0:
                self._schedule_next()
