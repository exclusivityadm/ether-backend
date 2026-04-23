from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, Field

from app.utils.projects import get_project


class ProviderStatus(BaseModel):
    project_slug: str
    enabled: Dict[str, bool] = Field(default_factory=dict)


def get_provider_status(project_slug: str) -> ProviderStatus:
    project = get_project(project_slug)
    if project is None:
        raise KeyError(project_slug)

    normalized = {name.lower(): bool(enabled) for name, enabled in project.provider_set.items()}
    return ProviderStatus(project_slug=project.slug, enabled=normalized)


def provider_enabled(project_slug: str, provider: str) -> bool:
    status = get_provider_status(project_slug)
    return bool(status.enabled.get((provider or "").strip().lower(), False))
