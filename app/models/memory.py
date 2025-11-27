from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.db import Base


class UnifyMemory(Base):
    """Primary long-term memory table for Ether.

    This is where we store merchant- and customer-scoped AI memories.
    """

    __tablename__ = "unify_memory"

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(
        String,
        nullable=True,
        index=True,
        doc="Composite scope: persona|merchant_id|customer_id|app_context",
    )
    key = Column(String, nullable=False, index=True)
    value = Column(Text, nullable=False)

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
