from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    return {"ok": True, "service": "Ether Backend v2"}
