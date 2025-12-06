from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), index=True)

    # raw image path or URL
    image_path = Column(String(512), nullable=True)

    # OCR raw text + normalized fields
    raw_text = Column(Text, nullable=True)
    vendor_name = Column(String(255), nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=True)
    tax = Column(Numeric(12, 2), nullable=True)
    total = Column(Numeric(12, 2), nullable=True)
    purchase_date = Column(Date, nullable=True)
    category = Column(String(128), nullable=True)

    # free-form JSON-ish for line items, tags, etc.
    metadata = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    merchant = relationship("Merchant", backref="receipts")
