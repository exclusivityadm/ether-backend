# app/routers/merchants.py

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app import models
from app.schemas.merchant import MerchantCreate, MerchantUpdate, MerchantResponse
from app.schemas.shared import SuccessResponse

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.post("/", response_model=MerchantResponse)
def create_merchant(payload: MerchantCreate, db: Session = Depends(get_db)):
    merchant = models.Merchant(
        name=payload.name,
        email=payload.email,
        external_ref=payload.external_ref,
        is_active=True,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@router.get("/", response_model=List[MerchantResponse])
def list_merchants(db: Session = Depends(get_db)):
    return db.query(models.Merchant).order_by(models.Merchant.created_at.desc()).all()


@router.get("/{merchant_id}", response_model=MerchantResponse)
def get_merchant(merchant_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Merchant not found.")
    return item


@router.patch("/{merchant_id}", response_model=MerchantResponse)
def update_merchant(merchant_id: int, payload: MerchantUpdate, db: Session = Depends(get_db)):
    item = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Merchant not found.")

    if payload.name is not None:
        item.name = payload.name
    if payload.email is not None:
        item.email = payload.email
    if payload.external_ref is not None:
        item.external_ref = payload.external_ref
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{merchant_id}", response_model=SuccessResponse)
def delete_merchant(merchant_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Merchant not found.")

    db.delete(item)
    db.commit()
    return SuccessResponse(message="Merchant deleted.")
