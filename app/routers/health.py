import os
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "service": "Ether Backend v2",
        "env": os.getenv("ENV", "local"),
    }
