from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class EtherErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNAUTHORIZED_CALLER = "UNAUTHORIZED_CALLER"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    DEPENDENCY_DOWN = "DEPENDENCY_DOWN"
    TIMEOUT = "TIMEOUT"
    INTERNAL = "INTERNAL"


class EtherError(BaseModel):
    """
    Standardized Ether error payload (internal only).
    """
    code: EtherErrorCode = Field(...)
    message: str = Field(...)
    request_id: Optional[str] = Field(None)
    details: Optional[dict[str, Any]] = Field(None)
