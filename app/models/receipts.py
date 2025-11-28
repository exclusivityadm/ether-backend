# app/models/receipts.py

from sqlalchemy import Column, Integer, String, DateTime, Float, Enum
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.models.base import Base    # <-- FIXED: import from base.py ONLY

class ReceiptSource(PyEnum):
    SOVA = "sova"
    NIRA = "nira"
    EASYKEEP = "easykeep"

class CurrencyCode(PyEnum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(String, nullable=False)
    source = Column(Enum(ReceiptSource), nullable=False)
    currency = Column(Enum(CurrencyCode), default=CurrencyCode.USD)
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
