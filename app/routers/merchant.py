from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.context.deps import get_current_merchant, get_db_dep
from app.db.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantRead

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.get("/me", response_model=MerchantRead)
def read_me(current: Merchant = Depends(get_current_merchant)) -> Merchant:
    return current


@router.post("", response_model=MerchantRead)
def create_merchant(
    payload: MerchantCreate,
    db: Session = Depends(get_db_dep),
) -> Merchant:
    merchant = Merchant(
        name=payload.name,
        email=payload.email,
        external_id=payload.external_id,
        timezone=payload.timezone,
        currency=payload.currency,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant
