"""Context router for Ether.

Exposes simple endpoints for inspecting the resolved tenant context.
This is primarily for debugging and verification during development
and early cloud deployment.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.context.deps import get_current_merchant
from app.models.merchant import Merchant

router = APIRouter(
    prefix="/context",
    tags=["context"],
)


@router.get("/whoami", summary="Return the resolved merchant identity")
async def whoami(
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    """Return basic information about the currently resolved merchant.

    This endpoint is especially useful for verifying that:
    - The correct merchant API key is being sent
    - The correct Merchant row is being loaded
    - Multi-tenant behavior is wired correctly
    """
    return {
        "id": merchant.id,
        "name": merchant.name,
        "store_domain": merchant.store_domain,
        "platform": merchant.platform,
    }


@router.get("/ping", summary="Simple ping endpoint for the context subsystem")
async def ping(
    db: Session = Depends(get_db),
) -> dict:
    """Basic sanity check that the DB is reachable and the context
    subsystem is mounted. Does not resolve a merchant.
    """
    # Simple DB round-trip to ensure connectivity
    db.execute("SELECT 1")
    return {"status": "ok", "context": "online"}
