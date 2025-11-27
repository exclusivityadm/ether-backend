from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantRead


def get_merchant(db: Session, merchant_id: int) -> Optional[Merchant]:
    return db.query(Merchant).filter(Merchant.id == merchant_id).first()


def get_merchant_by_email(db: Session, email: str) -> Optional[Merchant]:
    return db.query(Merchant).filter(Merchant.email == email).first()


def list_merchants(db: Session, skip: int = 0, limit: int = 50):
    return db.query(Merchant).offset(skip).limit(limit).all()


def create_merchant(db: Session, payload: MerchantCreate) -> Merchant:
    merchant = Merchant(
        name=payload.name,
        email=payload.email,
        status=getattr(payload, "status", "active") or "active",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def update_merchant_status(db: Session, merchant_id: int, status: str):
    merchant = get_merchant(db, merchant_id)
    if not merchant:
        return None
    merchant.status = status
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant
