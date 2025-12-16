# app/routers/health.py
from __future__ import annotations

from fastapi import APIRouter
from app.db.session import get_db_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    return {"ok": True, "service": "ether", "mode": "internal-only"}


@router.get("/deep")
async def deep_health():
    """
    Deep dependency checks (safe to expose; does not leak secrets).
    """
    checks = {
        "supabase": False,
        "db_read": False,
    }

    try:
        client = get_db_client()
        checks["supabase"] = True

        # lightweight read
        resp = client.table("ether_test").select("*").limit(1).execute()
        _ = resp.data
        checks["db_read"] = True
    except Exception:
        pass

    ok = all(checks.values())
    return {"ok": ok, "checks": checks}
