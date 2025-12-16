from typing import Optional
from pydantic import Field

from .core import EtherModel


class Ack(EtherModel):
    ok: bool = Field(True)
    request_id: Optional[str] = None
    message: str = "ack"


class IngestEventResponse(EtherModel):
    ok: bool = True
    request_id: Optional[str] = None
    event_id: str
    routed: bool = False
