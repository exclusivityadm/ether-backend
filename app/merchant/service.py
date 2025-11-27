
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.merchant import Merchant
from app.merchant.schemas import (
    MerchantCreate, MerchantUpdate, MerchantInDB, MerchantList
)

def create_merchant(db: Session, payload: MerchantCreate) -> MerchantInDB:
    obj = Merchant(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return MerchantInDB.model_validate(obj)

def get_merchant(db: Session, merchant_id: int):
    stmt = select(Merchant).where(Merchant.id == merchant_id)
    return db.execute(stmt).scalar_one_or_none()

def update_merchant(db: Session, merchant_id: int, payload: MerchantUpdate):
    obj = get_merchant(db, merchant_id)
    if obj is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return MerchantInDB.model_validate(obj)

def list_merchants(db: Session, skip=0, limit=50):
    stmt = select(Merchant).offset(skip).limit(limit)
    count_stmt = select(func.count()).select_from(Merchant)
    total = db.execute(count_stmt).scalar_one()
    items = [MerchantInDB.model_validate(m) for m in db.execute(stmt).scalars()]
    return MerchantList(items=items, total=total)

def delete_merchant(db: Session, merchant_id: int):
    obj = get_merchant(db, merchant_id)
    if obj is None:
        return None
    db.delete(obj)
    db.commit()
    return True
