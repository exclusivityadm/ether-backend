from fastapi import APIRouter
from apps.backend.utils.supabase_client import supabase

router = APIRouter(prefix="/db")

@router.get("/test")
async def db_test():
    return {"connected": supabase is not None}
