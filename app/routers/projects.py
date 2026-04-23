# app/routers/projects.py
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.schemas.errors import EtherErrorResponse
from app.utils.control_plane import control_plane_state
from app.utils.projects import get_project, list_projects as list_project_records, project_to_public_payload, resolve_project
from app.utils.request_meta import extract_request_meta

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectBootstrapRequest(BaseModel):
    project_slug: Optional[str] = None
    app_id: Optional[str] = None
    domain: Optional[str] = None


@router.get("")
async def list_projects():
    projects = [project_to_public_payload(project) for project in list_project_records()]
    return {
        "ok": True,
        "projects": projects,
        "count": len(projects),
    }


@router.get("/{project_slug}")
async def get_project_detail(project_slug: str):
    project = get_project(project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved.",
            details={"project_slug": project_slug},
        )

    payload = project_to_public_payload(project)
    payload["control_state"] = {
        "project_disabled": control_plane_state.project_disabled(project.slug),
    }
    return {"ok": True, "project": payload}


@router.post("/bootstrap")
async def bootstrap_project(request: Request, body: ProjectBootstrapRequest):
    meta = extract_request_meta(request)
    host = (request.headers.get("host") or "").strip() or None

    project = resolve_project(
        project_slug=body.project_slug or meta.project_slug,
        app_id=body.app_id or meta.app_id,
        app_domain=body.domain or host,
        source=meta.source,
    )

    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved.",
            details={
                "project_slug": body.project_slug or meta.project_slug,
                "app_id": body.app_id or meta.app_id,
                "domain": body.domain or host,
                "source": meta.source,
            },
        )

    resolved_by = "project_slug" if (body.project_slug or meta.project_slug) else "app_id" if (body.app_id or meta.app_id) else "domain_or_source"
    payload = project_to_public_payload(project)
    payload["control_state"] = {
        "project_disabled": control_plane_state.project_disabled(project.slug),
    }

    return {
        "ok": True,
        "project": payload,
        "resolved_by": resolved_by,
        "provider_summary": project.provider_set,
        "feature_flags": project.feature_flags,
    }
