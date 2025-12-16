# app/middleware/internal_auth.py

import hmac
import os
import logging
from fastapi import Header, HTTPException, status

log = logging.getLogger("ether_v2.security")

INTERNAL_KEY_HEADER = "X-Ether-Internal-Key"
SOURCE_HEADER = "X-Ether-Source"

def _env() -> str:
    return (os.getenv("APP_ENV", "dev") or "dev").lower()

def require_internal_access(
    x_ether_internal_key: str | None = Header(default=None, alias=INTERNAL_KEY_HEADER),
    x_ether_source: str | None = Header(default=None, alias=SOURCE_HEADER),
    # RequestMeta.source lives in the JSON body; we validate header-body match in the router.
):
    """
    Internal-only gate.

    Rules:
    - In staging/prod: ETHER_INTERNAL_KEY MUST be set and MUST match header.
    - In local/dev: if ETHER_INTERNAL_KEY is missing, we allow but log a warning.
    """
    env = _env()
    configured = os.getenv("ETHER_INTERNAL_KEY")

    if not configured:
        if env in ("prod", "production", "staging"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "DEPENDENCY_DOWN",
                    "message": "ETHER_INTERNAL_KEY is not configured for this environment",
                },
            )
        log.warning("[SECURITY] ETHER_INTERNAL_KEY missing; allowing internal access because APP_ENV=%s", env)
        return

    if not x_ether_internal_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED_CALLER", "message": f"Missing {INTERNAL_KEY_HEADER} header"},
        )

    # Constant-time compare
    if not hmac.compare_digest(x_ether_internal_key, configured):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Invalid internal access key"},
        )

    # Optional: you can require source header in prod/staging (recommended)
    if env in ("prod", "production", "staging") and not x_ether_source:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED_CALLER", "message": f"Missing {SOURCE_HEADER} header"},
        )
