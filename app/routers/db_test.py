# app/routers/db_test.py

from fastapi import APIRouter
from app.utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/db", tags=["supabase-db-test"])


@router.get("/tables")
async def list_test_table():
    """
    Reads from ether_test table to verify Supabase READ access.
    """
    client = get_supabase_client()
    try:
        result = client.table("ether_test").select("*", count="exact").limit(10).execute()
        return {
            "connected": True,
            "table": "ether_test",
            "records": result.data,
            "count": result.count
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


@router.post("/write")
async def write_test():
    """
    Writes into ether_test table to verify Supabase WRITE access.
    """
    client = get_supabase_client()
    try:
        result = client.table("ether_test").insert({"ts": "now"}).execute()
        return {"inserted": True, "response": result.data}
    except Exception as e:
        return {"inserted": False, "error": str(e)}
