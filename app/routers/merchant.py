
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

from app.db import get_db
from app.merchant.schemas import (
    MerchantCreate, MerchantUpdate, MerchantInDB, MerchantList
)
from app.merchant.service import (
    create_merchant, get_merchant, update_merchant,
    list_merchants, delete_merchant
)

router = APIRouter(prefix="/merchant", tags=["merchant"])

@router.post("", response_model=MerchantInDB)
async def create(payload: MerchantCreate, db: Session = Depends(get_db)):
    return create_merchant(db, payload)

@router.get("/{merchant_id}", response_model=MerchantInDB)
async def fetch(merchant_id: int, db: Session = Depends(get_db)):
    m = get_merchant(db, merchant_id)
    if m is None:
        raise HTTPException(HTTP_404_NOT_FOUND, "Merchant not found")
    return MerchantInDB.model_validate(m)

@router.get("", response_model=MerchantList)
async def list_all(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return list_merchants(db, skip, limit)

@router.put("/{merchant_id}", response_model=MerchantInDB)
async def update(merchant_id: int, payload: MerchantUpdate, db: Session = Depends(get_db)):
    updated = update_merchant(db, merchant_id, payload)
    if updated is None:
        raise HTTPException(HTTP_404_NOT_FOUND, "Merchant not found")
    return updated

@router.delete("/{merchant_id}")
async def delete(merchant_id: int, db: Session = Depends(get_db)):
    ok = delete_merchant(db, merchant_id)
    if not ok:
        raise HTTPException(HTTP_404_NOT_FOUND, "Merchant not found")
    return {"deleted": True}
