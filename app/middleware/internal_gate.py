# app/middleware/internal_gate.py
from __future__ import annotations

from typing import Iterable, Tuple, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.schemas.errors import EtherErrorResponse
from app.utils.request_meta import extract_request_meta


class InternalOnlyGate(BaseHTTPMiddleware):
    """
    Enforces Ether internal-only access.

    Rules:
    - Paths with exempt prefixes are always allowed (/, /health*, /version).
    - All other paths require X-ETHER-INTERNAL-TOKEN matching env ETHER_INTERNAL_TOKEN.
    - Optionally enforce source allowlist via X-ETHER-SOURCE header (exclusivity/sova/...)
    """

    def __init__(
        self,
        app,
        internal_token: str,
        allowed_sources: Iterable[str],
        exempt_prefixes: Tuple[str, ...] = ("/health", "/version", "/"),
    ):
        super().__init__(app)
        self.internal_token = internal_token or ""
        self.allowed_sources = set([s.strip() for s in allowed_sources if s.strip()])
        self.exempt_prefixes = exempt_prefixes

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path or "/"

        # Exempt routes
        for pfx in self.exempt_prefixes:
            if pfx == "/":
                if path == "/":
                    return await call_next(request)
                continue
            if path.startswith(pfx):
                return await call_next(request)

        # Must have a configured token
        if not self.internal_token:
            return EtherErrorResponse.unauthorized(
                code="ETHER_INTERNAL_TOKEN_NOT_SET",
                message="Ether is sealed; internal token is not configured.",
            )

        hdr = request.headers.get("X-ETHER-INTERNAL-TOKEN", "")
        if hdr != self.internal_token:
            return EtherErrorResponse.unauthorized(
                code="ETHER_UNAUTHORIZED",
                message="Missing or invalid internal token.",
            )

        # Optional: enforce source allowlist when header provided
        meta = extract_request_meta(request)
        if meta.source and self.allowed_sources and meta.source not in self.allowed_sources:
            return EtherErrorResponse.forbidden(
                code="ETHER_SOURCE_FORBIDDEN",
                message=f"Source '{meta.source}' is not allowed.",
                details={"allowed_sources": sorted(list(self.allowed_sources))},
            )

        return await call_next(request)
