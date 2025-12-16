# app/routers/health.py
from __future__ import annotations

from fastapi import APIRouter
from app.db.supabase import get_supabase_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    return {
        "ok": True,
        "service": "ether",
        "mode": "internal-only",
    }


@router.get("/deep")
async def deep_health():
    """
    Deep dependency checks.
    Safe to expose. No secrets. No stack traces.
    """
    checks = {
        "supabase_client": False,
        "db_read": False,
    }

    try:
        supabase = get_supabase_client()
        checks["supabase_client"] = True

        # lightweight read (table existence + connectivity)
        resp = supabase.table("ether_test").select("*").limit(1).execute()
        _ = resp.data
        checks["db_read"] = True
    except Exception:
        pass

    return {
        "ok": all(checks.values()),
        "checks": checks,
    }
