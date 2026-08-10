from __future__ import annotations

from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from statistics import median
from time import perf_counter
from typing import Deque, Dict, Iterator, List


@dataclass
class LatencySample:
    operation: str
    duration_ms: float


class LatencyRegistry:
    def __init__(self, max_samples_per_operation: int = 500) -> None:
        self._samples: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=max_samples_per_operation)
        )

    def record(self, operation: str, duration_ms: float) -> None:
        self._samples[operation].append(max(0.0, float(duration_ms)))

    @contextmanager
    def measure(self, operation: str) -> Iterator[None]:
        started = perf_counter()
        try:
            yield
        finally:
            self.record(operation, (perf_counter() - started) * 1000.0)

    def summary(self) -> Dict[str, dict]:
        return {name: self._summarize(values) for name, values in self._samples.items()}

    def _summarize(self, values: Deque[float]) -> dict:
        rows: List[float] = sorted(values)
        if not rows:
            return {"count": 0, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "max_ms": 0.0}

        def percentile(p: float) -> float:
            index = min(len(rows) - 1, max(0, int(round((len(rows) - 1) * p))))
            return rows[index]

        return {
            "count": len(rows),
            "p50_ms": round(median(rows), 3),
            "p95_ms": round(percentile(0.95), 3),
            "p99_ms": round(percentile(0.99), 3),
            "max_ms": round(rows[-1], 3),
        }


latency_registry = LatencyRegistry()
