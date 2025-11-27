
from typing import Optional
from pydantic import BaseModel, Field

class MerchantBase(BaseModel):
    name: Optional[str] = None
    store_domain: str
    platform: str = "custom"
    api_key: Optional[str] = None
    settings: dict = Field(default_factory=dict)

class MerchantCreate(MerchantBase):
    pass

class MerchantUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    settings: Optional[dict] = None

class MerchantInDB(MerchantBase):
    id: int
    class Config:
        from_attributes = True

class MerchantList(BaseModel):
    items: list[MerchantInDB]
    total: int
