from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.utils.audit import audit_event
from app.utils.project_supabase_signal import build_signal_payload, project_signal_readiness, record_project_signal
from app.utils.projects import get_project
from app.utils.request_meta import extract_request_meta

router = APIRouter(prefix="/operations", tags=["operations"])


class ProjectSignalOperationRequest(BaseModel):
    signal_kind: str = "manual"
    status: str = "ok"
    lane_id: Optional[str] = None
    app_id: Optional[str] = None
    instance_id: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


@router.get("/signal/readiness")
async def signal_readiness_index():
    return {
        "ok": True,
        "routes": {
            "project_readiness": "/readiness/{project_slug}",
            "manual_signal": "/operations/signal/{project_slug}",
        },
        "intended_use": "Internal-only readiness and manual signal operations for Render Cron, admin smoke tests, and wiring-day verification.",
    }


@router.post("/signal/{project_slug}")
async def trigger_project_signal(project_slug: str, body: ProjectSignalOperationRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(project_slug)
    if project is None:
        audit_event(
            action="operations.project_signal",
            project_slug=project_slug,
            actor=meta.source,
            result="project-not-found",
            details={"requested_project_slug": project_slug},
        )
        return {
            "ok": False,
            "error": {
                "code": "ETHER_PROJECT_NOT_FOUND",
                "message": "Project could not be resolved for operations signal.",
                "project_slug": project_slug,
            },
        }

    readiness = project_signal_readiness(project.slug).to_dict()
    payload = build_signal_payload(
        project_slug=project.slug,
        lane_id=body.lane_id or f"operations:{project.slug}",
        status=body.status,
        source=meta.source or "operations",
        app_id=body.app_id or project.slug,
        instance_id=body.instance_id or "manual-or-cron",
        heartbeat_count=0,
        verified=False,
        meta={
            "operation": body.signal_kind,
            "requested_by": meta.source,
            **body.meta,
        },
    )
    payload["signal_kind"] = body.signal_kind.strip() or "manual"

    result = record_project_signal(project_slug=project.slug, payload=payload).to_dict()
    audit_event(
        action="operations.project_signal",
        project_slug=project.slug,
        actor=meta.source,
        result="ok" if result.get("ok") else "failed",
        details={
            "readiness": readiness,
            "project_signal": result,
            "signal_kind": payload.get("signal_kind"),
        },
    )

    return {
        "ok": bool(result.get("ok")),
        "project_slug": project.slug,
        "readiness": readiness,
        "project_signal": result,
        "payload_summary": {
            "signal_kind": payload.get("signal_kind"),
            "lane_id": payload.get("lane_id"),
            "status": payload.get("status"),
            "app_id": payload.get("app_id"),
            "instance_id": payload.get("instance_id"),
        },
    }
