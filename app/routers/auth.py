# app/routers/auth.py
from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.auth import ProjectVerifyRequest, ProjectVerifyResponse
from app.schemas.errors import EtherErrorResponse
from app.utils.audit import audit_event
from app.utils.control_plane import control_plane_state
from app.utils.projects import resolve_project
from app.utils.request_meta import extract_request_meta
from app.utils.supabase_auth import verify_project_access_token

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

    if control_plane_state.project_disabled(project.slug):
        audit_event(
            action="auth.verify",
            project_slug=project.slug,
            actor=meta.source,
            result="project_disabled",
        )
        return EtherErrorResponse.forbidden(
            code="ETHER_PROJECT_DISABLED",
            message="Project is currently disabled by Ether control state.",
            details={"project_slug": project.slug},
        )

    verified = False
    verification_mode = "stub-pending-supabase"
    verified_user_id = body.user_id

    if body.access_token:
        verified, verification_mode, resolved_user_id = verify_project_access_token(project, body.access_token)
        if resolved_user_id:
            verified_user_id = resolved_user_id
    elif body.user_id:
        verified = True
        verification_mode = "user-id-present"

    audit_event(
        action="auth.verify",
        project_slug=project.slug,
        actor=meta.source,
        result="verified" if verified else "pending",
        details={
            "verification_mode": verification_mode,
            "role_hint": body.role_hint,
            "supabase_ready": bool(project.supabase_url and project.supabase_anon_key_configured),
        },
    )

    return ProjectVerifyResponse(
        ok=True,
        project_slug=project.slug,
        resolved_by="project_slug" if (body.project_slug or meta.project_slug) else "app_or_domain_or_source",
        verified=verified,
        verification_mode=verification_mode,
        user_id=verified_user_id,
        role_hint=body.role_hint,
    )
