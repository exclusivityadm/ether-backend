from typing import Optional
from pydantic import Field

from .core import EtherModel, EventEnvelope


class IngestEventRequest(EtherModel):
    event: EventEnvelope
    idempotency_key: Optional[str] = Field(None)
