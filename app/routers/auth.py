# app/routers/auth.py
from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.auth import ProjectVerifyRequest, ProjectVerifyResponse
from app.schemas.errors import EtherErrorResponse
from app.utils.audit import audit_event
from app.utils.projects import resolve_project
from app.utils.request_meta import extract_request_meta

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify", response_model=ProjectVerifyResponse)
async def verify_project_access(request: Request, body: ProjectVerifyRequest):
    meta = extract_request_meta(request)
    host = (request.headers.get("host") or "").strip() or None

    project = resolve_project(
        project_slug=body.project_slug or meta.project_slug,
        source=meta.source,
        app_domain=body.domain or host,
        app_id=body.app_id or meta.app_id,
    )
    if project is None:
        audit_event(
            action="auth.verify",
            project_slug=body.project_slug or meta.project_slug,
            actor=meta.source,
            result="project_not_found",
            details={"app_id": body.app_id or meta.app_id, "domain": body.domain or host},
        )
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for auth verification.",
            details={
                "project_slug": body.project_slug or meta.project_slug,
                "app_id": body.app_id or meta.app_id,
                "domain": body.domain or host,
                "source": meta.source,
            },
        )

    verified = bool(body.access_token or body.user_id)
    verification_mode = "token-present" if body.access_token else "user-id-present" if body.user_id else "stub-pending-supabase"

    audit_event(
        action="auth.verify",
        project_slug=project.slug,
        actor=meta.source,
        result="verified" if verified else "pending",
        details={"verification_mode": verification_mode, "role_hint": body.role_hint},
    )

    return ProjectVerifyResponse(
        ok=True,
        project_slug=project.slug,
        resolved_by="project_slug" if (body.project_slug or meta.project_slug) else "app_or_domain_or_source",
        verified=verified,
        verification_mode=verification_mode,
        user_id=body.user_id,
        role_hint=body.role_hint,
    )
