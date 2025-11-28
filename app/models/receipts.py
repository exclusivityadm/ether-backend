from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.sql import func
from .base import Base


class ReceiptSource(str, Enum):
    POS = "pos"
    UPLOADED = "uploaded"
    EMAIL = "email"
    MANUAL = "manual"


class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)

    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)

    source = Column(
        SAEnum(ReceiptSource, name="receipt_source_enum"),
        nullable=False,
    )

    currency = Column(
        SAEnum(CurrencyCode, name="currency_code_enum"),
        nullable=False,
        default=CurrencyCode.USD,
    )

    total_amount = Column(Float, nullable=False)
    vendor_name = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
