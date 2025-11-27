from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class GlobalCustomer(Base):
    """Global customer across all merchants.

    Every customer from every merchant is also represented here so Ether
    can learn across the entire ecosystem while still respecting merchant
    boundaries at the app level.
    """

    __tablename__ = "unify_global_customers"

    id = Column(Integer, primary_key=True, index=True)
    # A stable hashed or external ID (email, phone, wallet, etc.)
    global_key = Column(String, unique=True, index=True, nullable=False)

    email = Column(String, index=True, nullable=True)
    phone = Column(String, index=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    # Optional tags for clustering and future AI use
    tags = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    merchant_links = relationship("MerchantCustomer", back_populates="global_customer")


class MerchantCustomer(Base):
    """Customer as seen by a specific merchant.

    Links to GlobalCustomer but allows each merchant to have their own
    view of that customer (status, notes, loyalty state, etc.).
    """

    __tablename__ = "unify_merchant_customers"

    id = Column(Integer, primary_key=True, index=True)

    merchant_id = Column(Integer, index=True, nullable=False)

    global_customer_id = Column(
        Integer,
        ForeignKey("unify_global_customers.id", ondelete="SET NULL"),
        nullable=True,
    )

    email = Column(String, index=True, nullable=True)
    phone = Column(String, index=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    status = Column(String, nullable=True, default="active")
    segment = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    global_customer = relationship("GlobalCustomer", back_populates="merchant_links")
    events = relationship("CustomerEvent", back_populates="customer")


class CustomerEvent(Base):
    """Timeline of events for a merchant-specific customer.

    This captures purchases, loyalty events, campaigns, AI interactions, etc.
    """

    __tablename__ = "unify_customer_events"

    id = Column(Integer, primary_key=True, index=True)
    merchant_customer_id = Column(
        Integer,
        ForeignKey("unify_merchant_customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    merchant_id = Column(Integer, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)

    # Flexible JSON/text payload: order details, AI context, etc.
    extra_data = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    customer = relationship("MerchantCustomer", back_populates="events")
