# app/utils/project_registry.py
from __future__ import annotations

import json
from typing import Dict, Iterable, Optional, Tuple

from app.schemas.projects import (
    ProjectAdminSurface,
    ProjectBranding,
    ProjectProviderSet,
    ProjectRecord,
)
from app.utils.settings import settings


DEFAULT_PROJECTS = [
    ProjectRecord(
        project_slug="circa_haus",
        display_name="Circa Haus",
        status="planned",
        environment=settings.ETHER_ENVIRONMENT,
        app_domains=[],
        admin_domains=[],
        app_ids=["circa_haus", "salute", "origin_loft"],
        provider_set=ProjectProviderSet(
            supabase=True,
            stripe=True,
            twilio=True,
            openai=True,
            elevenlabs=True,
        ),
        feature_flags={
            "ether_control_plane": True,
            "provider_broker": True,
            "admin_surface": True,
        },
        branding=ProjectBranding(
            display_name="Circa Haus",
            primary_mark="vintage",
            tagline="The trusted home for creator independence",
        ),
        allowed_roles=["supporter", "creator", "admin"],
        admin_surface=ProjectAdminSurface(
            surface_id="circa_haus_admin",
            display_name="Circa Haus Admin",
            domain=None,
        ),
        webhook_routes={"stripe": "/webhooks/stripe", "twilio": "/webhooks/twilio"},
        notes="Former names: Salute, Origin Loft. Registered in Ether ahead of full app wiring.",
    ),
    ProjectRecord(
        project_slug="exclusivity",
        display_name="Exclusivity",
        status="active",
        environment=settings.ETHER_ENVIRONMENT,
        provider_set=ProjectProviderSet(supabase=True),
        feature_flags={"legacy_ingest": True},
        branding=ProjectBranding(display_name="Exclusivity"),
        allowed_roles=["merchant", "admin"],
        admin_surface=ProjectAdminSurface(
            surface_id="exclusivity_admin",
            display_name="Exclusivity Admin",
            domain=None,
        ),
        notes="Legacy/internal project preserved while Ether expands into multi-project control plane.",
    ),
    ProjectRecord(
        project_slug="sova",
        display_name="Sova",
        status="planned",
        environment=settings.ETHER_ENVIRONMENT,
        provider_set=ProjectProviderSet(supabase=True),
        feature_flags={"legacy_ingest": True},
        branding=ProjectBranding(display_name="Sova"),
        allowed_roles=["merchant", "admin"],
        admin_surface=ProjectAdminSurface(
            surface_id="sova_admin",
            display_name="Sova Admin",
            domain=None,
        ),
        notes="Local-only project placeholder so Ether can resolve Sova cleanly later.",
    ),
]


def _normalize(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.strip().lower()
    return v or None


class ProjectRegistry:
    def __init__(self, projects: Iterable[ProjectRecord]):
        self._projects: Dict[str, ProjectRecord] = {p.project_slug: p for p in projects}

    def all(self) -> Dict[str, ProjectRecord]:
        return dict(self._projects)

    def get(self, slug: str) -> Optional[ProjectRecord]:
        return self._projects.get(slug)

    def resolve(
        self,
        *,
        project_slug: Optional[str] = None,
        app_id: Optional[str] = None,
        domain: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Tuple[Optional[ProjectRecord], Optional[str]]:
        project_slug = _normalize(project_slug)
        app_id = _normalize(app_id)
        domain = _normalize(domain)
        source = _normalize(source)

        if project_slug and project_slug in self._projects:
            return self._projects[project_slug], "project_slug"

        for project in self._projects.values():
            normalized_app_ids = {_normalize(x) for x in project.app_ids}
            normalized_domains = {_normalize(x) for x in [*project.app_domains, *project.admin_domains]}

            if app_id and app_id in normalized_app_ids:
                return project, "app_id"
            if domain and domain in normalized_domains:
                return project, "domain"
            if source and source == _normalize(project.project_slug):
                return project, "source"

        return None, None



def _load_from_json(raw: str) -> Iterable[ProjectRecord]:
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("ETHER_PROJECT_REGISTRY_JSON must be a JSON array.")
    return [ProjectRecord.model_validate(item) for item in data]



def load_project_registry() -> ProjectRegistry:
    if settings.ETHER_PROJECT_REGISTRY_JSON:
        return ProjectRegistry(_load_from_json(settings.ETHER_PROJECT_REGISTRY_JSON))
    return ProjectRegistry(DEFAULT_PROJECTS)


project_registry = load_project_registry()
