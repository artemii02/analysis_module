from __future__ import annotations

from collections import Counter
from threading import Lock


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters = Counter(
            {
                "submissions_total": 0,
                "sync_submissions": 0,
                "async_submissions": 0,
                "reports_ready": 0,
                "reports_failed": 0,
            }
        )
        self._durations_ms: list[int] = []

    def record_submission(self, mode: str) -> None:
        with self._lock:
            self._counters["submissions_total"] += 1
            if mode == "sync":
                self._counters["sync_submissions"] += 1
            else:
                self._counters["async_submissions"] += 1

    def record_success(self, duration_ms: int) -> None:
        with self._lock:
            self._counters["reports_ready"] += 1
            self._durations_ms.append(duration_ms)

    def record_failure(self, duration_ms: int) -> None:
        with self._lock:
            self._counters["reports_failed"] += 1
            self._durations_ms.append(duration_ms)

    def snapshot(self) -> dict[str, int | float]:
        with self._lock:
            average_duration = 0.0
            if self._durations_ms:
                average_duration = round(sum(self._durations_ms) / len(self._durations_ms), 2)
            return {
                **self._counters,
                "average_duration_ms": average_duration,
            }
