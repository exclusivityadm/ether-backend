from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)

    vendor_name = Column(String(255), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(8), nullable=True, default="USD")
    purchase_date = Column(DateTime(timezone=True), nullable=True)

    raw_text = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")

    source = Column(String(50), nullable=True, default="upload")
    external_id = Column(String(255), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    merchant = relationship("Merchant", backref="receipts")
