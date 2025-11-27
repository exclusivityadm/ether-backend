# app/routers/receipts.py

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db import get_db
from app import models
from app.schemas.receipts import (
    ReceiptCreate,
    ReceiptResponse,
    ReceiptImageResponse,
)
from app.schemas.shared import SuccessResponse

router = APIRouter(prefix="/receipts", tags=["Receipts"])


# ----------------------------------------------------------
# Create receipt
# ----------------------------------------------------------
@router.post("/", response_model=ReceiptResponse)
def create_receipt(payload: ReceiptCreate, db: Session = Depends(get_db)):
    merchant = db.query(models.Merchant).filter(models.Merchant.id == payload.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found.")

    new_receipt = models.Receipt(
        merchant_id=payload.merchant_id,
        terminal_id=payload.terminal_id,
        source=payload.source,
        vendor_name=payload.vendor_name,
        subtotal_amount=payload.subtotal_amount,
        tax_amount=payload.tax_amount,
        total_amount=payload.total_amount,
        currency=payload.currency,
        raw_text=payload.raw_text,
        notes=payload.notes,
    )
    db.add(new_receipt)
    db.flush()  # ensures new_receipt.id exists

    # Line items
    for item in payload.line_items:
        li = models.ReceiptLineItem(
            receipt_id=new_receipt.id,
            category_id=item.category_id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
        )
        db.add(li)

    db.commit()
    db.refresh(new_receipt)
    return new_receipt


# ----------------------------------------------------------
# Upload image for receipt
# ----------------------------------------------------------
@router.post("/{receipt_id}/images", response_model=ReceiptImageResponse)
async def upload_receipt_image(
    receipt_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    receipt = db.query(models.Receipt).filter(models.Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found.")

    # For now we store a placeholder path
    storage_path = f"receipts/{receipt_id}/{image.filename}"

    img = models.ReceiptImage(
        receipt_id=receipt_id,
        storage_path=storage_path,
        mime_type=image.content_type,
    )
    db.add(img)
    db.commit()
    db.refresh(img)

    return img


# ----------------------------------------------------------
# Get receipts for a merchant
# ----------------------------------------------------------
@router.get("/merchant/{merchant_id}", response_model=List[ReceiptResponse])
def list_receipts_for_merchant(merchant_id: int, db: Session = Depends(get_db)):
    merchant = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found.")

    items = (
        db.query(models.Receipt)
        .filter(models.Receipt.merchant_id == merchant_id)
        .order_by(models.Receipt.created_at.desc())
        .all()
    )
    return items


# ----------------------------------------------------------
# Delete a receipt
# ----------------------------------------------------------
@router.delete("/{receipt_id}", response_model=SuccessResponse)
def delete_receipt(receipt_id: int, db: Session = Depends(get_db)):
    receipt = db.query(models.Receipt).filter(models.Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found.")

    db.delete(receipt)
    db.commit()
    return SuccessResponse(message="Receipt deleted.")
