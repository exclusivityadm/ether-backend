# app/routers/controls.py
from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.controls import ControlActionResponse, ProjectControlRequest, ProviderControlRequest
from app.schemas.errors import EtherErrorResponse
from app.utils.audit import audit_event
from app.utils.control_plane import control_plane_state
from app.utils.projects import get_project
from app.utils.request_meta import extract_request_meta

router = APIRouter(prefix="/controls", tags=["controls"])


@router.get("")
async def list_control_state():
    return {"ok": True, "controls": control_plane_state.snapshot()}


@router.post("/project/disable", response_model=ControlActionResponse)
async def disable_project(body: ProjectControlRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(body.project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for control action.",
            details={"project_slug": body.project_slug},
        )

    state = control_plane_state.disable_project(project.slug, body.reason, body.details)
    audit_event(
        action="controls.project.disable",
        project_slug=project.slug,
        actor=meta.source,
        result="disabled",
        details={"reason": body.reason, "details": body.details},
    )
    return ControlActionResponse(
        ok=True,
        control_type="project",
        project_slug=state.project_slug,
        status="disabled",
        reason=state.reason or body.reason,
    )


@router.post("/project/enable", response_model=ControlActionResponse)
async def enable_project(body: ProjectControlRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(body.project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for control action.",
            details={"project_slug": body.project_slug},
        )

    state = control_plane_state.enable_project(project.slug, body.reason, body.details)
    audit_event(
        action="controls.project.enable",
        project_slug=project.slug,
        actor=meta.source,
        result="enabled",
        details={"reason": body.reason, "details": body.details},
    )
    return ControlActionResponse(
        ok=True,
        control_type="project",
        project_slug=state.project_slug,
        status="enabled",
        reason=state.reason or body.reason,
    )


@router.post("/provider/disable", response_model=ControlActionResponse)
async def disable_provider(body: ProviderControlRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(body.project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for control action.",
            details={"project_slug": body.project_slug},
        )

    state = control_plane_state.disable_provider(project.slug, body.provider, body.reason, body.details)
    audit_event(
        action="controls.provider.disable",
        project_slug=project.slug,
        actor=meta.source,
        provider=state.provider,
        result="disabled",
        details={"reason": body.reason, "details": body.details},
    )
    return ControlActionResponse(
        ok=True,
        control_type="provider",
        project_slug=state.project_slug,
        provider=state.provider,
        status="disabled",
        reason=state.reason or body.reason,
    )


@router.post("/provider/enable", response_model=ControlActionResponse)
async def enable_provider(body: ProviderControlRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(body.project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for control action.",
            details={"project_slug": body.project_slug},
        )

    state = control_plane_state.enable_provider(project.slug, body.provider, body.reason, body.details)
    audit_event(
        action="controls.provider.enable",
        project_slug=project.slug,
        actor=meta.source,
        provider=state.provider,
        result="enabled",
        details={"reason": body.reason, "details": body.details},
    )
    return ControlActionResponse(
        ok=True,
        control_type="provider",
        project_slug=state.project_slug,
        provider=state.provider,
        status="enabled",
        reason=state.reason or body.reason,
    )
