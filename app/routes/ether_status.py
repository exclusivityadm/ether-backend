from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(
    prefix="/ether",
    tags=["ether-status"],
)


@router.get("/status")
async def ether_status():
    """
    Internal-only observability endpoint.

    This is NOT a health check.
    It answers: 'What state is Ether in right now?'
    """
    return {
        "service": "ether",
        "version": "2.0.1",
        "state": "authoritative",
        "contracts": "locked",
        "ingress": "strict",
        "egress": "stubbed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
