# app/models.py

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# ----------------------------------------------------------
# Enums
# ----------------------------------------------------------


class ReceiptSource(str, Enum):
    """
    Where the receipt/transaction originated.
    This lets us share Ether across Sova / Exclusivity / Nira.
    """
    SOVA = "sova"
    EXCLUSIVITY = "exclusivity"
    NIRA = "nira"
    MANUAL = "manual"


class CurrencyCode(str, Enum):
    """
    Minimal currency enum for now; expand as needed.
    """
    USD = "USD"


# ----------------------------------------------------------
# Core Entities
# ----------------------------------------------------------


class Merchant(Base):
    """
    A merchant using Ether (and Sova / Exclusivity / Nira).
    For now this can just be you, but this scales to multi-tenant later.
    """

    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_ref: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="External system ID (Shopify store id, etc.)"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    terminals: Mapped[List["Terminal"]] = relationship(
        "Terminal",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
    receipts: Mapped[List["Receipt"]] = relationship(
        "Receipt",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
    categories: Mapped[List["ReceiptCategory"]] = relationship(
        "ReceiptCategory",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )


class Terminal(Base):
    """
    A POS device / kiosk / app instance for Sova.
    """

    __tablename__ = "terminals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_ref: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Device id, serial, etc."
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="terminals",
    )
    receipts: Mapped[List["Receipt"]] = relationship(
        "Receipt",
        back_populates="terminal",
    )


class ReceiptCategory(Base):
    """
    Category for tax/write-off purposes (e.g., “Supplies”, “Marketing”).
    Shared by Sova, Exclusivity, and Nira through Ether.
    """

    __tablename__ = "receipt_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Internal or tax-code reference, if needed.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="categories",
    )
    line_items: Mapped[List["ReceiptLineItem"]] = relationship(
        "ReceiptLineItem",
        back_populates="category",
    )


class Receipt(Base):
    """
    Core receipt / transaction record.
    This is what Sova will write, and which Exclusivity/Nira can read later.
    """

    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    terminal_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("terminals.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    source: Mapped[ReceiptSource] = mapped_column(
        SAEnum(ReceiptSource, name="receipt_source_enum"),
        nullable=False,
        default=ReceiptSource.SOVA,
    )

    vendor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    subtotal_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    tax_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    currency: Mapped[CurrencyCode] = mapped_column(
        SAEnum(CurrencyCode, name="currency_code_enum"),
        nullable=False,
        default=CurrencyCode.USD,
    )

    raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Raw OCR text or original receipt text.",
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="receipts",
    )
    terminal: Mapped[Optional["Terminal"]] = relationship(
        "Terminal",
        back_populates="receipts",
    )
    line_items: Mapped[List["ReceiptLineItem"]] = relationship(
        "ReceiptLineItem",
        back_populates="receipt",
        cascade="all, delete-orphan",
    )
    images: Mapped[List["ReceiptImage"]] = relationship(
        "ReceiptImage",
        back_populates="receipt",
        cascade="all, delete-orphan",
    )


class ReceiptLineItem(Base):
    """
    Line items for a receipt (individual products / services).
    """

    __tablename__ = "receipt_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("receipt_categories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    description: Mapped[str] = mapped_column(String(512), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )
    line_total: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    receipt: Mapped["Receipt"] = relationship(
        "Receipt",
        back_populates="line_items",
    )
    category: Mapped[Optional["ReceiptCategory"]] = relationship(
        "ReceiptCategory",
        back_populates="line_items",
    )


class ReceiptImage(Base):
    """
    Reference to a stored receipt image (Supabase storage, S3, etc.).
    This lets Sova upload scans and Ether just keeps the pointer.
    """

    __tablename__ = "receipt_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        doc="Path or URL in storage (e.g. Supabase bucket key).",
    )
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    receipt: Mapped["Receipt"] = relationship(
        "Receipt",
        back_populates="images",
    )
