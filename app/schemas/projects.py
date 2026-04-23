# app/schemas/projects.py
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectBranding(BaseModel):
    display_name: str
    primary_mark: Optional[str] = None
    tagline: Optional[str] = None


class ProjectAdminSurface(BaseModel):
    surface_id: str
    display_name: str
    domain: Optional[str] = None


class ProjectProviderSet(BaseModel):
    supabase: bool = False
    stripe: bool = False
    twilio: bool = False
    openai: bool = False
    elevenlabs: bool = False


class ProjectRecord(BaseModel):
    project_slug: str
    display_name: str
    status: str = "planned"
    environment: str = "development"
    app_domains: List[str] = Field(default_factory=list)
    admin_domains: List[str] = Field(default_factory=list)
    app_ids: List[str] = Field(default_factory=list)
    provider_set: ProjectProviderSet = Field(default_factory=ProjectProviderSet)
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    branding: ProjectBranding
    allowed_roles: List[str] = Field(default_factory=lambda: ["user", "admin"])
    admin_surface: Optional[ProjectAdminSurface] = None
    webhook_routes: Dict[str, str] = Field(default_factory=dict)
    notes: Optional[str] = None


class ProjectBootstrapResponse(BaseModel):
    ok: bool = True
    project: ProjectRecord
    resolved_by: str
    provider_summary: Dict[str, bool]
    feature_flags: Dict[str, bool]
