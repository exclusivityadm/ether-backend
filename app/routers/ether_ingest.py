# app/routers/ether_ingest.py
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.schemas.errors import EtherErrorResponse
from app.utils.request_meta import extract_request_meta
from app.utils.settings import settings
from app.utils.safety import InMemoryRateLimiter, ReplayCache

router = APIRouter(prefix="/ether", tags=["ether"])

limiter = InMemoryRateLimiter(settings.ETHER_INGEST_RPM)
replay = ReplayCache(settings.ETHER_REPLAY_TTL_SECONDS)


class IngestEnvelope(BaseModel):
    """
    Minimal sealed ingest envelope.
    Your existing contracts layer can be stricter; this is a safe baseline.
    """
    type: str = Field(..., description="Event type, e.g. loyalty.purchase.created")
    ts: str = Field(..., description="ISO timestamp")
    payload: dict = Field(default_factory=dict)
    meta: dict = Field(default_factory=dict)


@router.post("/ingest")
async def ingest(request: Request, env: IngestEnvelope):
    # Body-size guard (FastAPI already parsed JSON; still enforce via header if present)
    cl = request.headers.get("content-length")
    if cl and int(cl) > settings.ETHER_MAX_BODY_BYTES:
        return EtherErrorResponse.too_large(
            code="ETHER_BODY_TOO_LARGE",
            message="Request body too large.",
            details={"max_bytes": settings.ETHER_MAX_BODY_BYTES},
        )

    meta = extract_request_meta(request)
    source = meta.source or "unknown"

    # RPM limit per source
    ok, retry_after = limiter.allow(source)
    if not ok:
        return EtherErrorResponse.rate_limited(
            code="ETHER_RATE_LIMITED",
            message="Rate limited.",
            details={"retry_after_seconds": retry_after, "source": source},
        )

    # Replay protection (idempotency)
    replay_key = meta.idempotency_key or meta.request_id
    if replay_key and replay.seen(f"{source}:{replay_key}"):
        return EtherErrorResponse.bad_request(
            code="ETHER_REPLAY_DETECTED",
            message="Duplicate request detected (idempotency).",
            details={"source": source},
        )

    # At this point the InternalOnlyGate already authenticated token + source allowlist.
    # Here is where you'd hand off into your contracts/ingress processor.
    # Keep it no-op-safe for now.
    return {"ok": True, "accepted": True, "source": source, "type": env.type}
