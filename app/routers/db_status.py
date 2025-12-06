# app/routers/db_status.py

from fastapi import APIRouter
from app.utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/db", tags=["supabase-status"])

@router.get("/status")
async def supabase_status():
    """
    Checks connection to Supabase auth URL (read-only connectivity probe)
    """
    try:
        client = get_supabase_client()
        # minimal call — no table access needed
        result = client.auth.get_session()
        return {
            "supabase_url_configured": True,
            "health_ok": True,
            "auth_session": str(result)
        }
    except Exception as e:
        return {
            "supabase_url_configured": True,
            "health_ok": False,
            "error": str(e)
        }
