# app/routers/projects.py
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.schemas.errors import EtherErrorResponse
from app.schemas.projects import ProjectBootstrapResponse
from app.utils.project_registry import project_registry
from app.utils.request_meta import extract_request_meta

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectBootstrapRequest(BaseModel):
    project_slug: Optional[str] = None
    app_id: Optional[str] = None
    domain: Optional[str] = None


@router.get("")
async def list_projects():
    return {
        "ok": True,
        "projects": [project.model_dump() for project in project_registry.all().values()],
        "count": len(project_registry.all()),
    }


@router.post("/bootstrap", response_model=ProjectBootstrapResponse)
async def bootstrap_project(request: Request, body: ProjectBootstrapRequest):
    meta = extract_request_meta(request)
    host = (request.headers.get("host") or "").strip() or None

    project, resolved_by = project_registry.resolve(
        project_slug=body.project_slug,
        app_id=body.app_id,
        domain=body.domain or host,
        source=meta.source,
    )

    if not project or not resolved_by:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved.",
            details={
                "project_slug": body.project_slug,
                "app_id": body.app_id,
                "domain": body.domain or host,
                "source": meta.source,
            },
        )

    return ProjectBootstrapResponse(
        ok=True,
        project=project,
        resolved_by=resolved_by,
        provider_summary=project.provider_set.model_dump(),
        feature_flags=project.feature_flags,
    )
