from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.utils.audit import audit_snapshot
from app.utils.control_plane import control_plane_state
from app.utils.phantom_core import phantom_core
from app.utils.phantom_keepalive import phantom_keepalive_lane
from app.utils.provider_readiness import provider_readiness_for_suite
from app.utils.sentinel import sentinel_engine
from app.utils.signal_verification_store import signal_verification_snapshot
from app.utils.webhook_store import webhook_snapshot

CORE_PROJECTS = ["circa_haus", "exclusivity"]
REQUIRED_SERVER_ENV = [
    "ETHER_INTERNAL_TOKEN",
    "ETHER_ALLOWED_SOURCES",
]
REQUIRED_CIRCA_HAUS_ENV = [
    "CIRCA_HAUS_SUPABASE_URL",
    "CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY",
    "CIRCA_HAUS_SIGNAL_RPC",
    "CIRCA_HAUS_SIGNAL_TABLE",
]
REQUIRED_EXCLUSIVITY_ENV = [
    "EXCLUSIVITY_SUPABASE_URL",
    "EXCLUSIVITY_SUPABASE_SERVICE_ROLE_KEY",
    "EXCLUSIVITY_SIGNAL_RPC",
    "EXCLUSIVITY_SIGNAL_TABLE",
]
PRODUCTION_SIGNATURE_ENV = [
    "CIRCA_HAUS_STRIPE_WEBHOOK_SECRET",
    "CIRCA_HAUS_CANVA_WEBHOOK_SECRET",
    "CIRCA_HAUS_APLIIQ_WEBHOOK_SECRET",
    "CIRCA_HAUS_PRINTFUL_WEBHOOK_SECRET",
]
OPTIONAL_BUT_EXPECTED_ENV = [
    "CIRCA_HAUS_TWILIO_AUTH_TOKEN",
    "CIRCA_HAUS_ETHER_SIGNAL_SECRET",
    "EXCLUSIVITY_ETHER_SIGNAL_SECRET",
]
PHANTOM_LAUNCH_BLOCKING_MODES = {"locked", "degraded", "safe_mode", "emergency_containment"}


def _present(key: str) -> bool:
    return bool(os.getenv(key, "").strip())


def _env_group(keys: List[str]) -> Dict[str, Any]:
    missing = [key for key in keys if not _present(key)]
    present = [key for key in keys if _present(key)]
    return {
        "ready": not missing,
        "present": present,
        "missing": missing,
    }


def _sentinel_status(project_slug: Optional[str] = None) -> Dict[str, Any]:
    snapshot = sentinel_engine.snapshot(project_slug=project_slug)
    blockers: List[str] = []
    open_threats = int(snapshot.get("threat_status_counts", {}).get("open", 0) or 0)
    active_quarantines = int(snapshot.get("quarantine_status_counts", {}).get("active", 0) or 0)
    quarantine_dispositions = int(snapshot.get("disposition_counts", {}).get("quarantine", 0) or 0)
    if open_threats:
        blockers.append(f"{open_threats} open Sentinel threat(s) require review.")
    if active_quarantines:
        blockers.append(f"{active_quarantines} active Sentinel quarantine(s) exist.")
    if quarantine_dispositions:
        blockers.append(f"{quarantine_dispositions} quarantine-level incident(s) are recorded.")
    return {
        "ready": not blockers,
        "blockers": blockers,
        "snapshot": snapshot,
    }


def _signal_status() -> Dict[str, Any]:
    snapshot = signal_verification_snapshot()
    last_success = snapshot.get("last_success_by_project", {})
    blockers = []
    for slug in CORE_PROJECTS:
        if not last_success.get(slug):
            blockers.append(f"No verified signal run exists for {slug}.")
    return {
        "ready": not blockers,
        "blockers": blockers,
        "snapshot": snapshot,
    }


def _control_status() -> Dict[str, Any]:
    snapshot = control_plane_state.snapshot()
    blockers = []
    for slug in snapshot.get("project_blockers", []):
        blockers.append(f"Project control disabled: {slug}")
    for key in snapshot.get("provider_blockers", []):
        blockers.append(f"Provider control disabled: {key}")
    return {
        "ready": not blockers,
        "blockers": blockers,
        "snapshot": snapshot,
    }


def _provider_status() -> Dict[str, Any]:
    readiness = provider_readiness_for_suite()
    blockers = []
    for project_slug, project_blockers in (readiness.get("launch_blockers") or {}).items():
        for blocker in project_blockers:
            blockers.append(f"{project_slug}: {blocker}")
    return {
        "ready": not blockers and bool(readiness.get("suite_launch_ready")),
        "blockers": blockers,
        "readiness": readiness,
    }


def _webhook_status() -> Dict[str, Any]:
    snapshots = {slug: webhook_snapshot(project_slug=slug) for slug in CORE_PROJECTS}
    blockers: List[str] = []
    for slug, snapshot in snapshots.items():
        status_counts = snapshot.get("status_counts") or {}
        invalid = int(status_counts.get("signature_invalid", 0) or 0)
        provider_disabled = int(status_counts.get("provider_disabled_by_control", 0) or 0)
        project_disabled = int(status_counts.get("project_disabled", 0) or 0)
        if invalid:
            blockers.append(f"{slug}: {invalid} invalid webhook signature event(s) observed.")
        if provider_disabled:
            blockers.append(f"{slug}: {provider_disabled} webhook event(s) rejected by provider control state.")
        if project_disabled:
            blockers.append(f"{slug}: {project_disabled} webhook event(s) rejected by project control state.")
    return {
        "ready": not blockers,
        "blockers": blockers,
        "snapshots": snapshots,
    }


def _phantom_status() -> Dict[str, Any]:
    status = phantom_core.status()
    keepalive = phantom_keepalive_lane.status()
    mode = status.get("mode")
    active_containments = status.get("active_containments") or []
    blockers: List[str] = []
    warnings: List[str] = []

    if mode in PHANTOM_LAUNCH_BLOCKING_MODES:
        blockers.append(f"Phantom Core mode is {mode}; production launch must remain no-go until recovered.")
    if active_containments:
        blockers.append(f"Phantom Core has {len(active_containments)} active containment(s).")

    last_error = keepalive.get("last_error")
    last_completed_at = keepalive.get("last_completed_at")
    run_count = int(keepalive.get("run_count") or 0)
    if last_error:
        blockers.append(f"Phantom keepalive lane is not clean: {last_error}")
    elif not last_completed_at or run_count < 1:
        warnings.append("Phantom keepalive lane has not completed a verified run yet; confirm before launch-day credentialing.")

    return {
        "ready": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "status": status,
        "keepalive": keepalive,
    }


def production_gate_snapshot(*, include_soft_warnings: bool = True) -> Dict[str, Any]:
    env = {
        "server": _env_group(REQUIRED_SERVER_ENV),
        "circa_haus": _env_group(REQUIRED_CIRCA_HAUS_ENV),
        "exclusivity": _env_group(REQUIRED_EXCLUSIVITY_ENV),
        "circa_haus_signatures": _env_group(PRODUCTION_SIGNATURE_ENV),
        "optional_expected": _env_group(OPTIONAL_BUT_EXPECTED_ENV),
    }
    env_blockers: List[str] = []
    for group_name in ["server", "circa_haus", "exclusivity", "circa_haus_signatures"]:
        missing = env[group_name]["missing"]
        for key in missing:
            env_blockers.append(f"Missing required env: {key}")

    soft_warnings: List[str] = []
    if include_soft_warnings:
        for key in env["optional_expected"]["missing"]:
            soft_warnings.append(f"Optional/expected env is not set yet: {key}")

    controls = _control_status()
    providers = _provider_status()
    sentinel_suite = _sentinel_status()
    signal = _signal_status()
    webhooks = _webhook_status()
    phantom = _phantom_status()
    audit = audit_snapshot(limit=30)

    if include_soft_warnings:
        soft_warnings.extend(phantom.get("warnings", []))

    blockers = []
    blockers.extend(env_blockers)
    blockers.extend(controls["blockers"])
    blockers.extend(providers["blockers"])
    blockers.extend(sentinel_suite["blockers"])
    blockers.extend(signal["blockers"])
    blockers.extend(webhooks["blockers"])
    blockers.extend(phantom["blockers"])

    sections = {
        "environment": env,
        "controls": controls,
        "providers": providers,
        "sentinel": sentinel_suite,
        "signal": signal,
        "webhooks": webhooks,
        "phantom_core": phantom,
        "audit": audit,
    }

    return {
        "ok": not blockers,
        "decision": "go" if not blockers else "no-go",
        "launch_ready": not blockers,
        "core_projects": list(CORE_PROJECTS),
        "blocker_count": len(blockers),
        "blockers": blockers,
        "soft_warning_count": len(soft_warnings),
        "soft_warnings": soft_warnings,
        "sections": sections,
        "operator_notes": [
            "A go decision means Ether has no known production gate blockers from configured checks.",
            "A no-go decision means clear every blocker before putting Ether in front of Circa Haus launch.",
            "Run POST /operations/suite/smoke after env wiring and before launch.",
            "Run POST /operations/cron/signal after Render cron is configured.",
            "Confirm /operations/signal/health has no launch blockers for Circa Haus or Exclusivity.",
            "Confirm /phantom/status and /phantom/keepalive/status show normal, verified state before launch.",
            "Emergency containment is an all-stop for dangerous writes, not a Phantom Core shutdown path.",
        ],
    }
