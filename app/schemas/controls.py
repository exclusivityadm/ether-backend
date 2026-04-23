# app/schemas/controls.py
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ProjectControlRequest(BaseModel):
    project_slug: str
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ProviderControlRequest(BaseModel):
    project_slug: str
    provider: str
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ControlActionResponse(BaseModel):
    ok: bool = True
    control_type: str
    project_slug: str
    provider: Optional[str] = None
    status: str
    reason: str
