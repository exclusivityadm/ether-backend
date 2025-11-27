# app/schemas/merchant.py

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class MerchantBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    external_ref: Optional[str] = None


class MerchantCreate(MerchantBase):
    name: str


class MerchantUpdate(MerchantBase):
    is_active: Optional[bool] = None


class MerchantResponse(MerchantBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
