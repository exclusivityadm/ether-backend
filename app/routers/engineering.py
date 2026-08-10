from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field

from app.schemas.errors import EtherErrorResponse
from app.utils.audit import audit_event
from app.utils.engineering_access import engineering_access_broker
from app.utils.request_meta import extract_request_meta

router = APIRouter(prefix="/engineering", tags=["engineering"])


class EngineeringTicketRequest(BaseModel):
    principal: str = "chatgpt-engineer"
    project_slug: str
    capabilities: List[str] = Field(default_factory=lambda: [
        "frontend.observe",
        "frontend.navigate",
        "backend.observe",
        "ether.observe",
        "logs.observe",
    ])
    ttl_seconds: int = 180
    metadata: Dict[str, str] = Field(default_factory=dict)


class EngineeringExchangeRequest(BaseModel):
    ticket: str


class EngineeringRevokeRequest(BaseModel):
    session_id: str


@router.post("/tickets")
async def issue_engineering_ticket(payload: EngineeringTicketRequest, request: Request):
    meta = extract_request_meta(request)
    result = engineering_access_broker.issue_ticket(
        principal=payload.principal,
        project_slug=payload.project_slug,
        capabilities=payload.capabilities,
        source=meta.source,
        ttl_seconds=payload.ttl_seconds,
        metadata=payload.metadata,
    )
    audit_event(
        action="engineering.ticket.issue",
        project_slug=payload.project_slug,
        actor=payload.principal,
        result="issued",
        details={"session_id": result["session"]["session_id"], "capabilities": payload.capabilities},
    )
    return {"ok": True, **result}


@router.post("/exchange")
async def exchange_engineering_ticket(payload: EngineeringExchangeRequest):
    result = engineering_access_broker.exchange_ticket(payload.ticket)
    if result is None:
        return EtherErrorResponse.unauthorized(
            code="ETHER_ENGINEERING_TICKET_INVALID",
            message="Engineering ticket is invalid, expired, revoked, or already consumed.",
        )
    session = result["session"]
    audit_event(
        action="engineering.ticket.exchange",
        project_slug=session["project_slug"],
        actor=session["principal"],
        result="accepted",
        details={"session_id": session["session_id"]},
    )
    return {"ok": True, **result}


@router.get("/session")
async def engineering_session(
    authorization: Optional[str] = Header(default=None),
):
    raw = (authorization or "").strip()
    bearer = raw[7:].strip() if raw.lower().startswith("bearer ") else ""
    record = engineering_access_broker.verify(bearer)
    if record is None:
        return EtherErrorResponse.unauthorized(
            code="ETHER_ENGINEERING_SESSION_INVALID",
            message="Engineering session is invalid or expired.",
        )
    return {
        "ok": True,
        "session": {
            "session_id": record.session_id,
            "principal": record.principal,
            "project_slug": record.project_slug,
            "capabilities": record.capabilities,
            "issued_at": record.issued_at,
            "expires_at": record.expires_at,
        },
    }


@router.post("/revoke")
async def revoke_engineering_session(payload: EngineeringRevokeRequest):
    count = engineering_access_broker.revoke(payload.session_id)
    return {"ok": True, "revoked_records": count}


@router.get("/sessions")
async def list_engineering_sessions():
    return {"ok": True, "sessions": engineering_access_broker.list_sessions()}
