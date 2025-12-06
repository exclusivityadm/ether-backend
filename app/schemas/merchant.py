from typing import Optional

from pydantic import BaseModel, EmailStr


class MerchantBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    timezone: Optional[str] = "UTC"
    currency: Optional[str] = "USD"


class MerchantCreate(MerchantBase):
    external_id: Optional[str] = None


class MerchantRead(MerchantBase):
    id: int
    external_id: Optional[str] = None
    onboarding_complete: bool = False

    class Config:
        from_attributes = True
