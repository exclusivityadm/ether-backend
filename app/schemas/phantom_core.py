from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PhantomGateRequest(BaseModel):
    project_slug: str
    action: str
    actor: str = "unknown"
    severity: str = "reversible_write"
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    provider: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    incident_id: Optional[str] = None


class PhantomContainmentRequest(BaseModel):
    reason: str
    actor: str = "owner"
    scope: str = "global"
    project_slug: Optional[str] = None
    provider: Optional[str] = None
    action_family: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    incident_id: Optional[str] = None


class PhantomRecoveryRequest(BaseModel):
    reason: str
    actor: str = "owner"
    scope: str = "global"
    project_slug: Optional[str] = None
    provider: Optional[str] = None
    action_family: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    incident_id: Optional[str] = None


class PhantomGateResponse(BaseModel):
    ok: bool = True
    decision: str
    mode: str
    action: str
    project_slug: str
    severity: str
    recovery_required: bool = False
    user_safe_message: str
    event_id: str
    notes: list[str] = Field(default_factory=list)
