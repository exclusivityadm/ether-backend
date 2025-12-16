# app/routers/version.py
from __future__ import annotations

import os
from fastapi import APIRouter

from app.utils.settings import settings

router = APIRouter(prefix="/version", tags=["observability"])


@router.get("")
async def version():
    """
    Stable fingerprint endpoint. Do NOT include secrets.
    """
    return {
        "service": "ether",
        "sealed": True,
        "version": settings.ETHER_VERSION,
        "git_sha": os.getenv("GIT_SHA", None),
        "cors_mode": settings.ETHER_CORS_MODE,
        "allowed_sources": list(settings.ETHER_ALLOWED_SOURCES),
    }
