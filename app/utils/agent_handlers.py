from __future__ import annotations

from typing import Any, Dict

from app.utils.agent_kernel import AgentJob, agent_kernel
from app.utils.latency import latency_registry
from app.utils.sentinel import sentinel_engine
from app.utils.web_intelligence import web_intelligence_registry


_MEMORY: Dict[tuple[str, str], Dict[str, Any]] = {}
_REGISTERED = False


def _web_observe(job: AgentJob) -> Dict[str, Any]:
    source_id = str(job.payload.get("source_id") or "").strip()
    content = str(job.payload.get("content") or "")
    evidence = job.payload.get("evidence") or {}
    if not source_id:
        raise ValueError("source_id is required")
    source = web_intelligence_registry.source(source_id)
    if source is None or source.project_slug != job.project_slug:
        raise PermissionError("source is not registered for this project")
    return web_intelligence_registry.record_observation(source_id, content, evidence)


def _web_route(job: AgentJob) -> Dict[str, Any]:
    return {
        "execution_path": web_intelligence_registry.choose_execution_path(
            requires_javascript=bool(job.payload.get("requires_javascript")),
            requires_interaction=bool(job.payload.get("requires_interaction")),
            authenticated=bool(job.payload.get("authenticated")),
        )
    }


def _web_changes(job: AgentJob) -> Dict[str, Any]:
    return {
        "changes": web_intelligence_registry.recent_changes(
            project_slug=job.project_slug,
            limit=int(job.payload.get("limit") or 100),
        )
    }


def _latency_summary(job: AgentJob) -> Dict[str, Any]:
    return {"project_slug": job.project_slug, "metrics": latency_registry.summary()}


def _security_snapshot(job: AgentJob) -> Dict[str, Any]:
    return {"project_slug": job.project_slug, "sentinel": sentinel_engine.snapshot(job.project_slug)}


def _memory_put(job: AgentJob) -> Dict[str, Any]:
    key = str(job.payload.get("key") or "").strip()
    if not key:
        raise ValueError("key is required")
    value = job.payload.get("value")
    _MEMORY[(job.project_slug, key)] = {"value": value, "evidence": job.payload.get("evidence") or {}}
    return {"stored": True, "key": key}


def _memory_get(job: AgentJob) -> Dict[str, Any]:
    key = str(job.payload.get("key") or "").strip()
    if not key:
        raise ValueError("key is required")
    return {"key": key, "record": _MEMORY.get((job.project_slug, key))}


def _memory_compact(job: AgentJob) -> Dict[str, Any]:
    prefix = str(job.payload.get("prefix") or "")
    rows = {
        key: value
        for (project, key), value in _MEMORY.items()
        if project == job.project_slug and (not prefix or key.startswith(prefix))
    }
    return {"count": len(rows), "records": rows}


def register_builtin_agent_handlers() -> None:
    global _REGISTERED
    if _REGISTERED:
        return

    agent_kernel.register_handler("web_intelligence", "observe", _web_observe)
    agent_kernel.register_handler("web_intelligence", "route", _web_route)
    agent_kernel.register_handler("web_intelligence", "changes", _web_changes)

    agent_kernel.register_handler("provider_intelligence", "observe", _web_observe)
    agent_kernel.register_handler("provider_intelligence", "changes", _web_changes)

    agent_kernel.register_handler("optimization", "latency_summary", _latency_summary)
    agent_kernel.register_handler("sentinel", "security_snapshot", _security_snapshot)
    agent_kernel.register_handler("recovery", "security_snapshot", _security_snapshot)

    agent_kernel.register_handler("memory", "put", _memory_put)
    agent_kernel.register_handler("memory", "get", _memory_get)
    agent_kernel.register_handler("memory", "compact", _memory_compact)
    _REGISTERED = True
