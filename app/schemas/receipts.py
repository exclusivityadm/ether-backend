from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class ReceiptLineItemCreate(BaseModel):
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    total: Optional[Decimal] = None
    category: Optional[str] = None


class ReceiptCreate(BaseModel):
    external_id: Optional[str] = None
    total: Optional[Decimal] = None
    currency: Optional[str] = None
    issued_at: Optional[datetime] = None
    notes: Optional[str] = None
    line_items: List[ReceiptLineItemCreate] = []


class ReceiptLineItemRead(ReceiptLineItemCreate):
    id: int

    class Config:
        from_attributes = True


class ReceiptImageRead(BaseModel):
    id: int
    storage_path: str
    mime_type: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ReceiptRead(BaseModel):
    id: int
    external_id: Optional[str] = None
    total: Optional[Decimal] = None
    currency: Optional[str] = None
    issued_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    line_items: List[ReceiptLineItemRead] = []
    images: List[ReceiptImageRead] = []

    class Config:
        from_attributes = True
