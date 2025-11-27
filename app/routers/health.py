from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Health check")
async def health_root():
    return {"status": "ok"}

@router.get("/deep", summary="Deep health check")
async def deep_health():
    return {
        "status": "ok",
        "checks": {
            "db": "pending",
            "openai": "pending",
            "services": []
        }
    }
