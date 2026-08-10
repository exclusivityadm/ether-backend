from __future__ import annotations

import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    capabilities: tuple[str, ...]
    projects: tuple[str, ...] = ("*",)
    description: str = ""


@dataclass
class CapabilityLease:
    token: str
    agent_name: str
    project_slug: str
    capabilities: tuple[str, ...]
    issued_at: str
    expires_at: str


@dataclass
class AgentJob:
    id: str
    agent_name: str
    project_slug: str
    operation: str
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "queued"
    created_at: str = field(default_factory=_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


Handler = Callable[[AgentJob], Dict[str, Any]]


class AgentKernel:
    """Project-agnostic execution registry for Ether specialist agents.

    Agents never receive database/provider credentials from this kernel.  They
    receive short-lived capability leases and call trusted Ether services for
    privileged operations.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, AgentDefinition] = {}
        self._handlers: Dict[tuple[str, str], Handler] = {}
        self._jobs: Dict[str, AgentJob] = {}
        self._leases: Dict[str, CapabilityLease] = {}

    def register_agent(self, definition: AgentDefinition) -> None:
        self._agents[definition.name] = definition

    def register_handler(self, agent_name: str, operation: str, handler: Handler) -> None:
        self._handlers[(agent_name, operation)] = handler

    def list_agents(self) -> List[dict]:
        return [asdict(item) for item in sorted(self._agents.values(), key=lambda row: row.name)]

    def issue_lease(
        self,
        *,
        agent_name: str,
        project_slug: str,
        requested_capabilities: List[str],
        ttl_seconds: int = 60,
    ) -> CapabilityLease:
        definition = self._agents.get(agent_name)
        if definition is None:
            raise ValueError("unknown agent")
        if "*" not in definition.projects and project_slug not in definition.projects:
            raise PermissionError("agent is not registered for this project")
        allowed = set(definition.capabilities)
        requested = tuple(sorted(set(requested_capabilities)))
        if any(capability not in allowed for capability in requested):
            raise PermissionError("requested capability exceeds agent authority")
        issued = _now()
        lease = CapabilityLease(
            token=secrets.token_urlsafe(32),
            agent_name=agent_name,
            project_slug=project_slug,
            capabilities=requested,
            issued_at=issued.isoformat(),
            expires_at=(issued + timedelta(seconds=max(5, min(ttl_seconds, 300)))).isoformat(),
        )
        self._leases[lease.token] = lease
        return lease

    def validate_lease(self, token: str, capability: str, project_slug: str) -> bool:
        lease = self._leases.get(token)
        if lease is None or lease.project_slug != project_slug or capability not in lease.capabilities:
            return False
        if datetime.fromisoformat(lease.expires_at) <= _now():
            self._leases.pop(token, None)
            return False
        return True

    def submit(self, *, agent_name: str, project_slug: str, operation: str, payload: Dict[str, Any]) -> AgentJob:
        if agent_name not in self._agents:
            raise ValueError("unknown agent")
        job = AgentJob(
            id=secrets.token_hex(12),
            agent_name=agent_name,
            project_slug=project_slug.strip().lower(),
            operation=operation,
            payload=dict(payload),
        )
        self._jobs[job.id] = job
        return job

    def run(self, job_id: str) -> AgentJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise ValueError("unknown job")
        handler = self._handlers.get((job.agent_name, job.operation))
        if handler is None:
            job.status = "rejected"
            job.error = "operation is not registered for this agent"
            job.completed_at = _now_iso()
            return job
        job.status = "running"
        job.started_at = _now_iso()
        try:
            job.result = handler(job)
            job.status = "completed"
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)[:500]
        job.completed_at = _now_iso()
        return job

    def get_job(self, job_id: str) -> Optional[dict]:
        job = self._jobs.get(job_id)
        return asdict(job) if job else None


agent_kernel = AgentKernel()

for definition in (
    AgentDefinition("web_intelligence", ("web:observe", "web:diff", "memory:write"), description="Observes registered external sources and records verified deltas."),
    AgentDefinition("sentinel", ("security:observe", "security:recommend"), description="Analyzes threat observations outside the transaction fast path."),
    AgentDefinition("optimization", ("latency:read", "optimization:recommend"), description="Analyzes Ether telemetry and recommends route/cache improvements."),
    AgentDefinition("provider_intelligence", ("provider:observe", "provider:diff", "memory:write"), description="Maintains provider capability and policy state."),
    AgentDefinition("recovery", ("operations:read", "recovery:recommend"), description="Builds recovery guidance from trusted operational evidence."),
    AgentDefinition("memory", ("memory:read", "memory:write", "memory:compact"), description="Maintains compact verified state for other Ether agents."),
):
    agent_kernel.register_agent(definition)
