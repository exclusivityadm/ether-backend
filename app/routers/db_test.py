# app/routers/db_test.py

from fastapi import APIRouter
from app.utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/db", tags=["supabase-test"])


@router.get("/tables")
async def list_tables():
    """
    Tests Supabase SELECT ability by reading from a known table.
    You may substitute 'profiles' with any existing table.
    """
    client = get_supabase_client()
    try:
        result = client.table("profiles").select("*", count="exact").limit(1).execute()
        return {
            "connected": True,
            "tables_accessible": True,
            "sample_record": result.data
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


@router.post("/write")
async def write_test():
    """
    Tests Supabase WRITE ability by inserting into ether_test table.
    """
    client = get_supabase_client()
    try:
        result = client.table("ether_test").insert({"ts": "now"}).execute()
        return {"inserted": True, "response": result.data}
    except Exception as e:
        return {"inserted": False, "error": str(e)}
