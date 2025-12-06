from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.context.deps import get_current_merchant, get_db_dep
from app.db.models.merchant import Merchant
from app.db.models.receipt import Receipt
from app.schemas.receipt import ReceiptCreate, ReceiptRead
from app.services.logging.log_service import log_event
from app.services.ocr.extractor import extract_text_from_image

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("", response_model=ReceiptRead)
async def create_receipt(
    payload: ReceiptCreate,
    db: Session = Depends(get_db_dep),
    merchant: Merchant = Depends(get_current_merchant),
) -> Receipt:
    receipt = Receipt(
        merchant_id=merchant.id,
        vendor_name=payload.vendor_name,
        subtotal=payload.subtotal,
        tax=payload.tax,
        total=payload.total,
        purchase_date=payload.purchase_date,
        category=payload.category,
        metadata=payload.metadata,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


@router.get("", response_model=List[ReceiptRead])
def list_receipts(
    db: Session = Depends(get_db_dep),
    merchant: Merchant = Depends(get_current_merchant),
) -> List[Receipt]:
    return (
        db.query(Receipt)
        .filter(Receipt.merchant_id == merchant.id)
        .order_by(Receipt.created_at.desc())
        .all()
    )


@router.post("/{receipt_id}/image", response_model=ReceiptRead)
async def upload_receipt_image(
    receipt_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_dep),
    merchant: Merchant = Depends(get_current_merchant),
) -> Receipt:
    receipt = (
        db.query(Receipt)
        .filter(
            Receipt.id == receipt_id,
            Receipt.merchant_id == merchant.id,
        )
        .first()
    )
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # persist file locally for v2
    contents = await file.read()
    folder = "storage/receipts"
    import os

    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{receipt_id}_{file.filename}")
    with open(path, "wb") as f:
        f.write(contents)

    receipt.image_path = path
    # call stub OCR
    receipt.raw_text = extract_text_from_image(path)
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    log_event("receipt_image_uploaded", {"receipt_id": receipt_id, "path": path})
    return receipt
