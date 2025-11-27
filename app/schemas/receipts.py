# app/schemas/receipts.py

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models import ReceiptSource, CurrencyCode


class LineItemInput(BaseModel):
    category_id: Optional[int] = None
    description: str
    quantity: float
    unit_price: float
    line_total: float


class ReceiptCreate(BaseModel):
    merchant_id: int
    terminal_id: Optional[int] = None
    source: ReceiptSource = ReceiptSource.SOVA

    vendor_name: Optional[str] = None
    subtotal_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: float
    currency: CurrencyCode = CurrencyCode.USD
    raw_text: Optional[str] = None
    notes: Optional[str] = None

    line_items: List[LineItemInput] = []


class ReceiptLineItemResponse(BaseModel):
    id: int
    description: str
    quantity: float
    unit_price: float
    line_total: float
    category_id: Optional[int]

    class Config:
        from_attributes = True


class ReceiptImageResponse(BaseModel):
    id: int
    storage_path: str
    mime_type: Optional[str]

    class Config:
        from_attributes = True


class ReceiptResponse(BaseModel):
    id: int
    merchant_id: int
    terminal_id: Optional[int]
    source: ReceiptSource

    vendor_name: Optional[str]
    transaction_date: datetime
    subtotal_amount: Optional[float]
    tax_amount: Optional[float]
    total_amount: float
    currency: CurrencyCode

    raw_text: Optional[str]
    notes: Optional[str]

    line_items: List[ReceiptLineItemResponse] = []
    images: List[ReceiptImageResponse] = []

    class Config:
        from_attributes = True
