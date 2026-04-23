# app/schemas/sentinel.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ThreatEventRequest(BaseModel):
    project_slug: Optional[str] = None
    app_id: Optional[str] = None
    domain: Optional[str] = None
    event_type: str
    severity: str = "medium"
    actor_id: Optional[str] = None
    source_ip: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ThreatEventResponse(BaseModel):
    ok: bool = True
    project_slug: str
    event_type: str
    severity: str
    risk_score: int
    disposition: str
    quarantined: bool


class QuarantineRequest(BaseModel):
    project_slug: str
    target_type: str
    target_id: str
    reason: str
    expires_at: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class QuarantineResponse(BaseModel):
    ok: bool = True
    project_slug: str
    target_type: str
    target_id: str
    status: str
    reason: str


class ThreatReviewRequest(BaseModel):
    project_slug: Optional[str] = None
    recent_limit: int = 10


class ThreatReviewResponse(BaseModel):
    ok: bool = True
    project_slug: Optional[str] = None
    ai_mode: str
    summary: str
    recommended_actions: List[str] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)
