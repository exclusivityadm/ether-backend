import logging
import os

import httpx
from fastapi import APIRouter

from app.utils.supabase_client import get_supabase_client, SupabaseNotConfigured

router = APIRouter(prefix="/db", tags=["db"])
logger = logging.getLogger("ether_v2.db_status")


@router.get("/test")
async def db_test() -> dict:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    result: dict = {
        "supabase_url_configured": bool(supabase_url),
        "health_ok": False,
        "error": None,
    }

    if not supabase_url:
        result["error"] = "SUPABASE_URL not set"
        return result

    try:
        _ = get_supabase_client()
    except SupabaseNotConfigured as exc:
        result["error"] = str(exc)
        return result
    except Exception as exc:
        logger.exception("Unexpected error creating Supabase client: %s", exc)
        result["error"] = f"Unexpected client error: {exc}"
        return result

    health_url = supabase_url.rstrip("/") + "/auth/v1/health"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(health_url)
        result["health_ok"] = resp.status_code == 200
        if not result["health_ok"]:
            result["error"] = f"Supabase health returned status {resp.status_code}"
    except Exception as exc:
        logger.warning("Error calling Supabase health endpoint: %s", exc)
        result["error"] = f"Supabase health request failed: {exc}"

    return result
