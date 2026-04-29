from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SignalHandshakeRequest(BaseModel):
    project_slug: Optional[str] = None
    app_id: Optional[str] = None
    domain: Optional[str] = None
    bundle_id: Optional[str] = None
    lane_id: Optional[str] = None
    instance_id: Optional[str] = None
    client_nonce: Optional[str] = None
    presented_proof: Optional[str] = None
    requested_capabilities: List[str] = Field(default_factory=list)


class SignalHandshakeResponse(BaseModel):
    ok: bool = True
    project_slug: str
    resolved_by: str
    lane_id: str
    accepted: bool
    verified: bool
    verification_mode: str
    proof_required: bool
    signal_ready: bool
    server_nonce: str
    next_heartbeat_seconds: int
    control_state: Dict[str, bool]
    provider_controls: Dict[str, bool]
    feature_flags: Dict[str, bool]


class SignalHeartbeatRequest(BaseModel):
    project_slug: Optional[str] = None
    app_id: Optional[str] = None
    domain: Optional[str] = None
    lane_id: str
    instance_id: Optional[str] = None
    status: str = "ok"
    client_nonce: Optional[str] = None
    presented_proof: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class SignalHeartbeatResponse(BaseModel):
    ok: bool = True
    project_slug: str
    lane_id: str
    accepted: bool
    verified: bool
    verification_mode: str
    proof_required: bool
    keepalive_recorded: bool
    server_nonce: str
    next_heartbeat_seconds: int
    control_state: Dict[str, bool]
    provider_controls: Dict[str, bool]
    project_signal: Dict[str, Any] = Field(default_factory=dict)
