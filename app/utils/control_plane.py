# app/utils/control_plane.py
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from app.utils.control_store import (
    init_control_store,
    list_control_events,
    load_control_snapshot,
    save_control_event,
    save_project_control,
    save_provider_control,
)

log = logging.getLogger("ether_v2.control_plane")


@dataclass
class ProjectControlState:
    project_slug: str
    disabled: bool = False
    reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    updated_at: Optional[str] = None


@dataclass
class ProviderControlState:
    project_slug: str
    provider: str
    disabled: bool = False
    reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    updated_at: Optional[str] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ControlPlaneState:
    def __init__(self) -> None:
        self._projects: Dict[str, ProjectControlState] = {}
        self._providers: Dict[Tuple[str, str], ProviderControlState] = {}
        self._loaded = False

    def initialize(self) -> None:
        try:
            init_control_store()
            snapshot = load_control_snapshot()
            self._projects = {
                slug: ProjectControlState(
                    project_slug=slug,
                    disabled=bool(row.get("disabled")),
                    reason=row.get("reason"),
                    details=row.get("details") or {},
                    updated_at=row.get("updated_at"),
                )
                for slug, row in snapshot.get("projects", {}).items()
            }
            self._providers = {}
            for key, row in snapshot.get("providers", {}).items():
                project_slug = (row.get("project_slug") or "").strip().lower()
                provider = (row.get("provider") or "").strip().lower()
                if not project_slug or not provider:
                    continue
                self._providers[(project_slug, provider)] = ProviderControlState(
                    project_slug=project_slug,
                    provider=provider,
                    disabled=bool(row.get("disabled")),
                    reason=row.get("reason"),
                    details=row.get("details") or {},
                    updated_at=row.get("updated_at"),
                )
            self._loaded = True
        except Exception as exc:
            self._loaded = False
            log.warning("ether_control_plane_initialize_failed=%s", exc)

    def _record_event(
        self,
        *,
        control_type: str,
        action: str,
        project_slug: str,
        provider: Optional[str],
        reason: Optional[str],
        actor: Optional[str],
        incident_id: Optional[str],
        details: Dict[str, Any],
        created_at: str,
    ) -> Dict[str, Any]:
        try:
            return save_control_event(
                control_type=control_type,
                action=action,
                project_slug=project_slug,
                provider=provider,
                reason=reason,
                actor=actor,
                incident_id=incident_id,
                details=details,
                created_at=created_at,
            )
        except Exception as exc:
            log.warning("ether_control_plane_event_save_failed=%s", exc)
            return {}

    def disable_project(
        self,
        project_slug: str,
        reason: str,
        details: Dict[str, Any],
        *,
        actor: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> ProjectControlState:
        slug = project_slug.strip().lower()
        updated_at = _now()
        enriched_details = dict(details or {})
        if incident_id:
            enriched_details.setdefault("incident_id", incident_id)
        state = ProjectControlState(project_slug=slug, disabled=True, reason=reason, details=enriched_details, updated_at=updated_at)
        self._projects[slug] = state
        try:
            save_project_control(project_slug=slug, disabled=True, reason=reason, details=enriched_details, updated_at=updated_at)
        except Exception as exc:
            log.warning("ether_control_plane_project_save_failed=%s", exc)
        self._record_event(
            control_type="project",
            action="disable",
            project_slug=slug,
            provider=None,
            reason=reason,
            actor=actor,
            incident_id=incident_id,
            details=enriched_details,
            created_at=updated_at,
        )
        return state

    def enable_project(
        self,
        project_slug: str,
        reason: str,
        details: Dict[str, Any],
        *,
        actor: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> ProjectControlState:
        slug = project_slug.strip().lower()
        updated_at = _now()
        enriched_details = dict(details or {})
        if incident_id:
            enriched_details.setdefault("incident_id", incident_id)
        state = ProjectControlState(project_slug=slug, disabled=False, reason=reason, details=enriched_details, updated_at=updated_at)
        self._projects[slug] = state
        try:
            save_project_control(project_slug=slug, disabled=False, reason=reason, details=enriched_details, updated_at=updated_at)
        except Exception as exc:
            log.warning("ether_control_plane_project_save_failed=%s", exc)
        self._record_event(
            control_type="project",
            action="enable",
            project_slug=slug,
            provider=None,
            reason=reason,
            actor=actor,
            incident_id=incident_id,
            details=enriched_details,
            created_at=updated_at,
        )
        return state

    def disable_provider(
        self,
        project_slug: str,
        provider: str,
        reason: str,
        details: Dict[str, Any],
        *,
        actor: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> ProviderControlState:
        slug = project_slug.strip().lower()
        provider_key = provider.strip().lower()
        updated_at = _now()
        key = (slug, provider_key)
        enriched_details = dict(details or {})
        if incident_id:
            enriched_details.setdefault("incident_id", incident_id)
        state = ProviderControlState(project_slug=slug, provider=provider_key, disabled=True, reason=reason, details=enriched_details, updated_at=updated_at)
        self._providers[key] = state
        try:
            save_provider_control(project_slug=slug, provider=provider_key, disabled=True, reason=reason, details=enriched_details, updated_at=updated_at)
        except Exception as exc:
            log.warning("ether_control_plane_provider_save_failed=%s", exc)
        self._record_event(
            control_type="provider",
            action="disable",
            project_slug=slug,
            provider=provider_key,
            reason=reason,
            actor=actor,
            incident_id=incident_id,
            details=enriched_details,
            created_at=updated_at,
        )
        return state

    def enable_provider(
        self,
        project_slug: str,
        provider: str,
        reason: str,
        details: Dict[str, Any],
        *,
        actor: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> ProviderControlState:
        slug = project_slug.strip().lower()
        provider_key = provider.strip().lower()
        updated_at = _now()
        key = (slug, provider_key)
        enriched_details = dict(details or {})
        if incident_id:
            enriched_details.setdefault("incident_id", incident_id)
        state = ProviderControlState(project_slug=slug, provider=provider_key, disabled=False, reason=reason, details=enriched_details, updated_at=updated_at)
        self._providers[key] = state
        try:
            save_provider_control(project_slug=slug, provider=provider_key, disabled=False, reason=reason, details=enriched_details, updated_at=updated_at)
        except Exception as exc:
            log.warning("ether_control_plane_provider_save_failed=%s", exc)
        self._record_event(
            control_type="provider",
            action="enable",
            project_slug=slug,
            provider=provider_key,
            reason=reason,
            actor=actor,
            incident_id=incident_id,
            details=enriched_details,
            created_at=updated_at,
        )
        return state

    def project_disabled(self, project_slug: str) -> bool:
        state = self._projects.get(project_slug.strip().lower())
        return bool(state and state.disabled)

    def provider_disabled(self, project_slug: str, provider: str) -> bool:
        key = (project_slug.strip().lower(), (provider or "").strip().lower())
        state = self._providers.get(key)
        return bool(state and state.disabled)

    def events(
        self,
        *,
        project_slug: Optional[str] = None,
        provider: Optional[str] = None,
        incident_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        try:
            return list_control_events(project_slug=project_slug, provider=provider, incident_id=incident_id, limit=limit)
        except Exception as exc:
            log.warning("ether_control_plane_events_read_failed=%s", exc)
            return []

    def snapshot(self) -> Dict[str, Any]:
        project_blockers = [slug for slug, state in self._projects.items() if state.disabled]
        provider_blockers = [
            f"{slug}:{provider}"
            for (slug, provider), state in self._providers.items()
            if state.disabled
        ]
        return {
            "loaded_from_store": self._loaded,
            "launch_blocking": bool(project_blockers or provider_blockers),
            "project_blockers": project_blockers,
            "provider_blockers": provider_blockers,
            "projects": {
                slug: {
                    "disabled": state.disabled,
                    "reason": state.reason,
                    "details": state.details,
                    "updated_at": state.updated_at,
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
                    "updated_at": state.updated_at,
                }
                for (slug, provider), state in self._providers.items()
            },
        }


control_plane_state = ControlPlaneState()
