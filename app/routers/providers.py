# app/routers/providers.py
from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.errors import EtherErrorResponse
from app.utils.audit import audit_event
from app.utils.provider_broker import get_provider_status
from app.utils.request_meta import extract_request_meta

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/{project_slug}")
async def provider_status(project_slug: str, request: Request):
    meta = extract_request_meta(request)
    try:
        status = get_provider_status(project_slug)
    except KeyError:
        audit_event(
            action="providers.status",
            project_slug=project_slug,
            actor=meta.source,
            result="project_not_found",
        )
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for provider status.",
            details={"project_slug": project_slug},
        )

    audit_event(
        action="providers.status",
        project_slug=project_slug,
        actor=meta.source,
        result="ok",
    )
    return {"ok": True, "provider_status": status.model_dump()}
