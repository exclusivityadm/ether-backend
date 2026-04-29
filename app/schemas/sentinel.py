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
    threat_id: Optional[int] = None


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
    quarantine_id: Optional[int] = None


class QuarantineReleaseRequest(BaseModel):
    quarantine_id: int
    reason: str


class ThreatReviewRequest(BaseModel):
    project_slug: Optional[str] = None
    recent_limit: int = 10


class ThreatManualReviewRequest(BaseModel):
    threat_id: int
    status: str = "reviewed"
    review_notes: Optional[str] = None


class ThreatReviewResponse(BaseModel):
    ok: bool = True
    project_slug: Optional[str] = None
    ai_mode: str
    summary: str
    recommended_actions: List[str] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)


class SentinelStatusResponse(BaseModel):
    ok: bool = True
    project_slug: Optional[str] = None
    snapshot: Dict[str, Any] = Field(default_factory=dict)
    launch_blocking: bool = False
    launch_blockers: List[str] = Field(default_factory=list)
