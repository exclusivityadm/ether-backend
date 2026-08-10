from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.utils.agent_kernel import agent_kernel
from app.utils.latency import latency_registry
from app.utils.web_intelligence import WebSource, web_intelligence_registry

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class WebSourceRequest(BaseModel):
    id: str
    project_slug: str
    kind: str
    url: str
    authority: str = "authoritative"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ObservationRequest(BaseModel):
    content: str
    evidence: Dict[str, Any] = Field(default_factory=dict)


class RouteDecisionRequest(BaseModel):
    requires_javascript: bool = False
    requires_interaction: bool = False
    authenticated: bool = False


class AgentJobRequest(BaseModel):
    agent_name: str
    project_slug: str
    operation: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class LeaseRequest(BaseModel):
    agent_name: str
    project_slug: str
    capabilities: List[str] = Field(default_factory=list)
    ttl_seconds: int = 60


@router.get("/agents")
async def list_agents():
    return {"ok": True, "agents": agent_kernel.list_agents()}


@router.post("/agents/lease")
async def issue_agent_lease(body: LeaseRequest):
    lease = agent_kernel.issue_lease(
        agent_name=body.agent_name,
        project_slug=body.project_slug.strip().lower(),
        requested_capabilities=body.capabilities,
        ttl_seconds=body.ttl_seconds,
    )
    return {
        "ok": True,
        "lease": {
            "agent_name": lease.agent_name,
            "project_slug": lease.project_slug,
            "capabilities": lease.capabilities,
            "issued_at": lease.issued_at,
            "expires_at": lease.expires_at,
        },
        "token": lease.token,
    }


@router.post("/agents/jobs")
async def submit_agent_job(body: AgentJobRequest):
    job = agent_kernel.submit(
        agent_name=body.agent_name,
        project_slug=body.project_slug.strip().lower(),
        operation=body.operation,
        payload=body.payload,
    )
    return {"ok": True, "job": agent_kernel.get_job(job.id)}


@router.post("/agents/jobs/{job_id}/run")
async def run_agent_job(job_id: str):
    job = agent_kernel.run(job_id)
    return {"ok": job.status == "completed", "job": agent_kernel.get_job(job.id)}


@router.get("/agents/jobs/{job_id}")
async def get_agent_job(job_id: str):
    job = agent_kernel.get_job(job_id)
    return {"ok": job is not None, "job": job}


@router.post("/web/sources")
async def register_web_source(body: WebSourceRequest):
    source = web_intelligence_registry.register_source(
        WebSource(
            id=body.id,
            project_slug=body.project_slug.strip().lower(),
            kind=body.kind,
            url=body.url,
            authority=body.authority,
            metadata=body.metadata,
        )
    )
    return {"ok": True, "source": source.__dict__}


@router.get("/web/sources")
async def list_web_sources(project_slug: Optional[str] = None):
    return {"ok": True, "sources": web_intelligence_registry.list_sources(project_slug)}


@router.post("/web/sources/{source_id}/observations")
async def record_web_observation(source_id: str, body: ObservationRequest):
    result = web_intelligence_registry.record_observation(source_id, body.content, body.evidence)
    return {"ok": True, "observation": result}


@router.get("/web/changes")
async def recent_web_changes(project_slug: Optional[str] = None, limit: int = 100):
    return {"ok": True, "changes": web_intelligence_registry.recent_changes(project_slug, limit)}


@router.post("/web/route")
async def choose_web_route(body: RouteDecisionRequest):
    path = web_intelligence_registry.choose_execution_path(
        requires_javascript=body.requires_javascript,
        requires_interaction=body.requires_interaction,
        authenticated=body.authenticated,
    )
    return {"ok": True, "execution_path": path}


@router.get("/latency")
async def latency_summary():
    return {"ok": True, "metrics": latency_registry.summary()}
