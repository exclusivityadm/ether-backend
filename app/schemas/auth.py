# app/schemas/auth.py
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ProjectVerifyRequest(BaseModel):
    project_slug: Optional[str] = None
    app_id: Optional[str] = None
    domain: Optional[str] = None
    access_token: Optional[str] = None
    user_id: Optional[str] = None
    role_hint: Optional[str] = None


class ProjectVerifyResponse(BaseModel):
    ok: bool = True
    project_slug: str
    resolved_by: str
    verified: bool
    verification_mode: str
    user_id: Optional[str] = None
    role_hint: Optional[str] = None
