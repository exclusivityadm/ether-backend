from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum as SAEnum,
    Numeric,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.db import Base


# -------------------------------------------
# Receipt Source Enum
# -------------------------------------------
class ReceiptSource(str, Enum):
    SOVA = "sova"
    EXCLUSIVITY = "exclusivity"
    NIRASOVA = "nirasova"


# -------------------------------------------
# Currency Enum
# -------------------------------------------
class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"


# -------------------------------------------
# Receipt Model
# -------------------------------------------
class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, nullable=False)

    source = Column(SAEnum(ReceiptSource), nullable=False)
    currency = Column(SAEnum(CurrencyCode), nullable=False)

    vendor_name = Column(String, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationship → line_items table
    line_items = relationship("LineItem", back_populates="receipt")


# -------------------------------------------
# Line Items for Receipts
# -------------------------------------------
class LineItem(Base):
    __tablename__ = "receipt_line_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False)

    description = Column(String, nullable=True)
    category = Column(String, nullable=True)
    amount = Column(Numeric(10, 2), nullable=True)

    receipt = relationship("Receipt", back_populates="line_items")
