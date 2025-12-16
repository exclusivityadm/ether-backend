from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator


class EtherModel(BaseModel):
    """
    Base for all Ether contracts:
    - strict field enforcement
    - immutable by default
    """
    model_config = ConfigDict(extra="forbid", frozen=True)


class EtherSource(str, Enum):
    EXCLUSIVITY = "exclusivity"
    SOVA = "sova"
    NIRASOVA_OS = "nirasova_os"
    ADMIN = "admin"


class RequestMeta(EtherModel):
    source: EtherSource
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex}")
    trace_id: Optional[str] = None
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    environment: Literal["local", "dev", "staging", "prod"] = "dev"

    @field_validator("emitted_at")
    @classmethod
    def ensure_tz(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


class MerchantRef(EtherModel):
    merchant_id: str
    platform: Literal["shopify", "square", "manual", "unknown"] = "unknown"
    external_store_id: Optional[str] = None


class CustomerRef(EtherModel):
    customer_id: str
    merchant_id: str


class LedgerRef(EtherModel):
    ledger_id: str
    domain: Literal["exclusivity", "sova", "nirasova_os"]


class EtherEventType(str, Enum):
    MERCHANT_CREATED = "merchant.created"
    MERCHANT_UPDATED = "merchant.updated"
    CUSTOMER_UPSERTED = "customer.upserted"

    PURCHASE_RECORDED = "purchase.recorded"
    LOYALTY_POLICY_UPDATED = "loyalty.policy_updated"
    LOYALTY_LEDGER_MUTATED = "loyalty.ledger_mutated"

    AI_INTERACTION = "ai.interaction"

    SYSTEM_HEALTH = "system.health"
    SYSTEM_AUDIT = "system.audit"


class EventEnvelope(EtherModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex}")
    event_type: EtherEventType
    meta: RequestMeta
    merchant: MerchantRef
    customer: Optional[CustomerRef] = None
    ledger: Optional[LedgerRef] = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("payload")
    @classmethod
    def payload_is_dict(cls, v: Any) -> dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("payload must be a dict")
        return v
