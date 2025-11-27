from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


# ------------------------------------------------------------
# Base shared fields
# ------------------------------------------------------------
class MerchantBase(BaseModel):
    name: str = Field(..., description="Merchant's business name")
    email: EmailStr = Field(..., description="Merchant contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    status: Optional[str] = Field(default="active", description="Account status")


# ------------------------------------------------------------
# For creating (POST /merchants)
# ------------------------------------------------------------
class MerchantCreate(MerchantBase):
    password: str = Field(..., min_length=6, description="Password for merchant login")


# ------------------------------------------------------------
# For reading a merchant record
# ------------------------------------------------------------
class MerchantRead(MerchantBase):
    id: UUID = Field(..., description="Merchant unique ID")

    class Config:
        from_attributes = True  # replaces orm_mode
