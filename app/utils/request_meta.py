# app/utils/request_meta.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from starlette.requests import Request


@dataclass(frozen=True)
class RequestMeta:
    source: Optional[str] = None  # exclusivity/sova/nirasova_os/admin
    request_id: Optional[str] = None
    idempotency_key: Optional[str] = None


def extract_request_meta(request: Request) -> RequestMeta:
    return RequestMeta(
        source=(request.headers.get("X-ETHER-SOURCE") or "").strip() or None,
        request_id=(request.headers.get("X-REQUEST-ID") or "").strip() or None,
        idempotency_key=(request.headers.get("X-IDEMPOTENCY-KEY") or "").strip() or None,
    )
