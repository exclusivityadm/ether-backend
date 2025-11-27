from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict


class GlobalCustomerBase(BaseModel):
    global_key: str = Field(..., description="Stable cross-merchant customer key")
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tags: Optional[str] = None


class GlobalCustomerCreate(GlobalCustomerBase):
    pass


class GlobalCustomerRead(GlobalCustomerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MerchantCustomerBase(BaseModel):
    merchant_id: int
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[str] = "active"
    segment: Optional[str] = None
    notes: Optional[str] = None
    global_key: Optional[str] = Field(
        None,
        description="If provided, link this merchant customer to a GlobalCustomer by global_key",
    )


class MerchantCustomerCreate(MerchantCustomerBase):
    pass


class MerchantCustomerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[str] = None
    segment: Optional[str] = None
    notes: Optional[str] = None


class MerchantCustomerRead(MerchantCustomerBase):
    id: int
    global_customer_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CustomerEventBase(BaseModel):
    merchant_id: int
    merchant_customer_id: int
    event_type: str
    description: Optional[str] = None
    extra_data: Optional[str] = Field(
        None,
        description="Flexible JSON or text payload for order details, AI context, etc.",
    )


class CustomerEventCreate(CustomerEventBase):
    pass


class CustomerEventRead(CustomerEventBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MerchantCustomerWithEvents(MerchantCustomerRead):
    events: List[CustomerEventRead] = []
