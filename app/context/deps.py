from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.merchant import Merchant
from app.db.session import get_db

settings = get_settings()


def get_db_dep() -> Generator:
    yield from get_db()


def get_current_merchant(
    db: Session = Depends(get_db_dep),
) -> Merchant:
    """
    For v2, we keep this super simple:
      - assume a single default merchant row for now
      - later we can wire to API key / JWT once Sova & Exclusivity are ready.
    """
    merchant = db.query(Merchant).first()
    if not merchant:
        merchant = Merchant(name="Default Merchant", email=None)
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
    return merchant
