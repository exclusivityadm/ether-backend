# app/routers/webhooks.py
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Request

from app.schemas.errors import EtherErrorResponse
from app.utils.audit import audit_event
from app.utils.control_plane import control_plane_state
from app.utils.projects import get_project
from app.utils.provider_broker import provider_enabled
from app.utils.request_meta import extract_request_meta

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/{provider}/{project_slug}")
async def ingest_webhook(
    provider: str,
    project_slug: str,
    request: Request,
    payload: Dict[str, Any] = Body(default_factory=dict),
):
    meta = extract_request_meta(request)
    project = get_project(project_slug)
    if project is None:
        audit_event(
            action="webhook.ingest",
            project_slug=project_slug,
            actor=meta.source,
            provider=provider,
            result="project_not_found",
        )
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for webhook ingestion.",
            details={"project_slug": project_slug, "provider": provider},
        )

    if control_plane_state.project_disabled(project.slug):
        audit_event(
            action="webhook.ingest",
            project_slug=project.slug,
            actor=meta.source,
            provider=provider,
            result="project_disabled",
        )
        return EtherErrorResponse.forbidden(
            code="ETHER_PROJECT_DISABLED",
            message="Project is currently disabled by Ether control state.",
            details={"project_slug": project.slug, "provider": provider},
        )

    if control_plane_state.provider_disabled(project.slug, provider):
        audit_event(
            action="webhook.ingest",
            project_slug=project.slug,
            actor=meta.source,
            provider=provider,
            result="provider_disabled_by_control",
        )
        return EtherErrorResponse.forbidden(
            code="ETHER_PROVIDER_DISABLED_BY_CONTROL",
            message="Provider is currently disabled by Ether control state.",
            details={"project_slug": project.slug, "provider": provider},
        )

    if not provider_enabled(project_slug, provider):
        audit_event(
            action="webhook.ingest",
            project_slug=project_slug,
            actor=meta.source,
            provider=provider,
            result="provider_disabled",
        )
        return EtherErrorResponse.forbidden(
            code="ETHER_PROVIDER_DISABLED",
            message="Provider is not enabled for this project.",
            details={"project_slug": project_slug, "provider": provider},
        )

    configured_route = project.webhook_routes.get(provider.lower())
    audit_event(
        action="webhook.ingest",
        project_slug=project_slug,
        actor=meta.source,
        provider=provider,
        result="accepted",
        details={"configured_route": configured_route, "payload_keys": sorted(list(payload.keys()))[:20]},
    )

    return {
        "ok": True,
        "accepted": True,
        "project_slug": project_slug,
        "provider": provider.lower(),
        "configured_route": configured_route,
    }
