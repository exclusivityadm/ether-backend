# app/utils/safety.py
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Tuple


class InMemoryRateLimiter:
    """
    Best-effort in-memory RPM limiter (per key). Good enough for internal sealing.
    If you later add Redis, we can swap implementations without changing callers.
    """

    def __init__(self, rpm: int):
        self.rpm = max(1, int(rpm))
        self.window_seconds = 60
        self.buckets: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> Tuple[bool, Optional[int]]:
        now = time.time()
        q = self.buckets[key]

        # drop old
        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()

        if len(q) >= self.rpm:
            retry_after = int(q[0] + self.window_seconds - now) + 1
            return False, max(1, retry_after)

        q.append(now)
        return True, None


class ReplayCache:
    """
    Best-effort replay protection using an in-memory TTL cache.
    Keys should be idempotency keys or request ids.
    """

    def __init__(self, ttl_seconds: int):
        self.ttl = max(1, int(ttl_seconds))
        self.store: Dict[str, float] = {}

    def seen(self, key: str) -> bool:
        now = time.time()
        # sweep occasionally
        if len(self.store) > 20000:
            self._sweep(now)
        exp = self.store.get(key)
        if exp and exp > now:
            return True
        self.store[key] = now + self.ttl
        return False

    def _sweep(self, now: float) -> None:
        dead = [k for k, exp in self.store.items() if exp <= now]
        for k in dead:
            self.store.pop(k, None)
