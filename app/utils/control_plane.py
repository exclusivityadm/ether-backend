# app/utils/control_plane.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class ProjectControlState:
    project_slug: str
    disabled: bool = False
    reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderControlState:
    project_slug: str
    provider: str
    disabled: bool = False
    reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class ControlPlaneState:
    def __init__(self) -> None:
        self._projects: Dict[str, ProjectControlState] = {}
        self._providers: Dict[Tuple[str, str], ProviderControlState] = {}

    def disable_project(self, project_slug: str, reason: str, details: Dict[str, Any]) -> ProjectControlState:
        state = ProjectControlState(project_slug=project_slug, disabled=True, reason=reason, details=details)
        self._projects[project_slug] = state
        return state

    def enable_project(self, project_slug: str, reason: str, details: Dict[str, Any]) -> ProjectControlState:
        state = ProjectControlState(project_slug=project_slug, disabled=False, reason=reason, details=details)
        self._projects[project_slug] = state
        return state

    def disable_provider(self, project_slug: str, provider: str, reason: str, details: Dict[str, Any]) -> ProviderControlState:
        key = (project_slug, provider.strip().lower())
        state = ProviderControlState(project_slug=project_slug, provider=key[1], disabled=True, reason=reason, details=details)
        self._providers[key] = state
        return state

    def enable_provider(self, project_slug: str, provider: str, reason: str, details: Dict[str, Any]) -> ProviderControlState:
        key = (project_slug, provider.strip().lower())
        state = ProviderControlState(project_slug=project_slug, provider=key[1], disabled=False, reason=reason, details=details)
        self._providers[key] = state
        return state

    def project_disabled(self, project_slug: str) -> bool:
        state = self._projects.get(project_slug)
        return bool(state and state.disabled)

    def provider_disabled(self, project_slug: str, provider: str) -> bool:
        key = (project_slug, (provider or "").strip().lower())
        state = self._providers.get(key)
        return bool(state and state.disabled)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "projects": {
                slug: {
                    "disabled": state.disabled,
                    "reason": state.reason,
                    "details": state.details,
                }
                for slug, state in self._projects.items()
            },
            "providers": {
                f"{slug}:{provider}": {
                    "project_slug": state.project_slug,
                    "provider": state.provider,
                    "disabled": state.disabled,
                    "reason": state.reason,
                    "details": state.details,
                }
                for (slug, provider), state in self._providers.items()
            },
        }


control_plane_state = ControlPlaneState()
