from __future__ import annotations

from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.utils.latency import latency_registry


class EtherLatencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = perf_counter()
        try:
            return await call_next(request)
        finally:
            duration_ms = (perf_counter() - started) * 1000.0
            latency_registry.record(f"http:{request.method}:{request.url.path}", duration_ms)
