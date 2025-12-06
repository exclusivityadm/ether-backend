from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ReceiptBase(BaseModel):
    vendor_name: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    purchase_date: Optional[date] = None
    category: Optional[str] = None
    metadata: Optional[str] = None


class ReceiptCreate(ReceiptBase):
    pass


class ReceiptRead(ReceiptBase):
    id: int
    merchant_id: int
    image_path: Optional[str] = None
    raw_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
