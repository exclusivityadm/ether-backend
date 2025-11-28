# app/models/receipts.py

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base   # ← FIXED: import Base directly
from .receipts_enums import ReceiptSource, CurrencyCode
