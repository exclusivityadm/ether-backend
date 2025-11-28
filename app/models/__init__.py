# app/models/__init__.py

from .base import Base
from .merchant import Merchant

# DO NOT import receipts here — it causes circular imports.
# Import only the enums (safe, no SQLAlchemy metadata creation)
from .receipts_enums import ReceiptSource, CurrencyCode

__all__ = [
    "Base",
    "Merchant",
    "ReceiptSource",
    "CurrencyCode",
]
