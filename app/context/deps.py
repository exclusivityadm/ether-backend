"""Context and multi-tenant helpers for Ether.

This module centralizes logic for resolving the *current merchant*
based on the incoming request. It is intentionally simple and safe:

- Looks for an `X-Merchant-Api-Key` header
- Uses that to look up a Merchant row
- If none is found, raises a 401
- Returns the Merchant instance for downstream use

This powers multi-tenant behavior for:
- Sova POS
- Exclusivity
- NiraSova OS
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED

from app.db import get_db
from app.models.merchant import Merchant


async def get_current_merchant(
    db: Session = Depends(get_db),
    x_merchant_api_key: Optional[str] = Header(
        default=None,
        alias="X-Merchant-Api-Key",
        description="Per-merchant API key used to resolve tenant context.",
    ),
) -> Merchant:
    """Resolve the current Merchant based on the API key header.

    If no header is provided or the key is invalid, this will raise
    a 401 error. This prevents cross-tenant data leakage and ensures
    only requests with a valid merchant API key are processed.
    """
    if not x_merchant_api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Missing X-Merchant-Api-Key header.",
        )

    merchant = (
        db.query(Merchant)
        .filter(Merchant.api_key == x_merchant_api_key)
        .one_or_none()
    )

    if merchant is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid merchant API key.",
        )

    return merchant
