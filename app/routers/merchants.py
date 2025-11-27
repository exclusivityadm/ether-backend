from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.merchant import MerchantCreate, MerchantRead
from app.repositories.merchants import (
    get_merchant,
    get_merchant_by_email,
    list_merchants,
    create_merchant,
    update_merchant_status,
)

router = APIRouter(
    prefix="/merchants",
    tags=["merchants"],
)


@router.get("/", response_model=List[MerchantRead])
def list_all_merchants(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[MerchantRead]:
    return list_merchants(db, skip=skip, limit=limit)


@router.get("/{merchant_id}", response_model=MerchantRead)
def read_merchant(
    merchant_id: int,
    db: Session = Depends(get_db),
) -> MerchantRead:
    merchant = get_merchant(db, merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found",
        )
    return merchant


@router.post(
    "/",
    response_model=MerchantRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_merchant(
    payload: MerchantCreate,
    db: Session = Depends(get_db),
) -> MerchantRead:
    existing = get_merchant_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A merchant with this email already exists.",
        )
    merchant = create_merchant(db, payload)
    return merchant


@router.patch("/{merchant_id}/status", response_model=MerchantRead)
def set_merchant_status(
    merchant_id: int,
    status_value: str,
    db: Session = Depends(get_db),
) -> MerchantRead:
    merchant = update_merchant_status(db, merchant_id, status=status_value)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found",
        )
    return merchant
