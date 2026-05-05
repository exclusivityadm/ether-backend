from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from app.utils.audit import audit_event, list_recent_audit_events

PHANTOM_MODES = {"normal", "degraded", "safe_mode", "owner_recovery", "emergency_containment", "locked"}

SEVERITY_READ = "read"
SEVERITY_HARMLESS_WRITE = "harmless_write"
SEVERITY_REVERSIBLE_WRITE = "reversible_write"
SEVERITY_IRREVERSIBLE_WRITE = "irreversible_write"
SEVERITY_SOVEREIGNTY_CRITICAL = "sovereignty_critical"

DANGEROUS_SEVERITIES = {SEVERITY_IRREVERSIBLE_WRITE, SEVERITY_SOVEREIGNTY_CRITICAL}
SAFE_SEVERITIES = {SEVERITY_READ, SEVERITY_HARMLESS_WRITE}

DEFAULT_IRREVERSIBLE_ACTIONS = {
    "admin.elevate",
    "admin.transfer_ownership",
    "admin.grant_root_access",
    "controls.project.disable",
    "controls.project.enable",
    "controls.provider.disable",
    "controls.provider.enable",
    "controls.recover",
    "provider.rotate_key",
    "provider.disable_critical",
    "provider.enable_critical",
    "provider.change_payment_rail",
    "payments.enable_payouts",
    "payments.release_payout",
    "payments.refund_override",
    "ledger.mutate_receipt",
    "ledger.backfill_financial_record",
    "policy.override_version",
    "policy.force_acknowledgement",
    "phantom.change_mode",
    "phantom.recover",
    "phantom.policy_change",
    "ether.global_config_change",
    "ether.route_override",
    "ether.deploy_sensitive_change",
    "circa.finalize_creator_onboarding",
    "circa.enable_creator_payouts",
    "circa.subscription_override",
}

OWNER_INVARIANTS = [
    "No admin elevation or ownership transfer may proceed while authority is ambiguous.",
    "No provider key rotation may proceed without a recorded reason and owner-level actor context.",
    "No payout enablement or payout release may proceed during emergency containment.",
    "No ledger or receipt mutation may proceed without an explicit registered action and audit record.",
    "No policy version override may proceed silently or without a sovereignty event.",
    "No ordinary app or provider control may disable Phantom Core observation or logging.",
    "If Phantom Core is unhealthy, dangerous writes pause while safe reads remain available.",
    "Emergency containment stops hazardous autonomous behavior without deleting history.",
]

USER_SAFE_MESSAGES = {
    "allow": "The requested operation is cleared to proceed.",
    "pause": "This action is temporarily paused for safety review. Your progress has been preserved.",
    "deny": "This action cannot proceed in the current safety state.",
}


@dataclass
class PhantomContainment:
    scope: str
    reason: str
    actor: str
    ts: str
    project_slug: Optional[str] = None
    provider: Optional[str] = None
    action_family: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    incident_id: Optional[str] = None
    active: bool = True


class PhantomCoreEngine:
    def __init__(self) -> None:
        self._lock = Lock()
        self.mode = "normal"
        self.mode_reason = "Phantom Core initialized."
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.last_heartbeat = self.started_at
        self.irreversible_actions = set(DEFAULT_IRREVERSIBLE_ACTIONS)
        self.containments: List[PhantomContainment] = []
        self.policy_version = "phantom-core-launch-v1"

    def initialize(self) -> None:
        with self._lock:
            self.mode = "normal"
            self.last_heartbeat = datetime.now(timezone.utc).isoformat()
        audit_event(
            action="phantom.initialize",
            result="ok",
            details={"mode": self.mode, "policy_version": self.policy_version, "invariants": OWNER_INVARIANTS},
        )

    def heartbeat(self) -> Dict[str, Any]:
        with self._lock:
            self.last_heartbeat = datetime.now(timezone.utc).isoformat()
            return self.status()

    def status(self) -> Dict[str, Any]:
        active_containments = [c for c in self.containments if c.active]
        return {
            "ok": True,
            "name": "Ether Phantom Core",
            "mode": self.mode,
            "mode_reason": self.mode_reason,
            "started_at": self.started_at,
            "last_heartbeat": self.last_heartbeat,
            "policy_version": self.policy_version,
            "always_on": True,
            "casual_disable_supported": False,
            "emergency_containment_supported": True,
            "active_containment_count": len(active_containments),
            "active_containments": [self._containment_dict(c) for c in active_containments],
            "registered_irreversible_action_count": len(self.irreversible_actions),
            "registered_irreversible_actions": sorted(self.irreversible_actions),
            "owner_invariants": OWNER_INVARIANTS,
            "operator_notes": [
                "Phantom Core is always on with bounded authority.",
                "Emergency containment limits enforcement cascades without disabling observation or logging.",
                "Dangerous writes pause when Phantom Core is contained, degraded, locked, or uncertain.",
                "Safe reads and harmless actions should remain available when practical.",
            ],
        }

    def containment(self, *, reason: str, actor: str, scope: str = "global", project_slug: Optional[str] = None, provider: Optional[str] = None, action_family: Optional[str] = None, details: Optional[Dict[str, Any]] = None, incident_id: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        containment = PhantomContainment(
            scope=scope,
            reason=reason,
            actor=actor,
            ts=now,
            project_slug=project_slug,
            provider=provider,
            action_family=action_family,
            details=details or {},
            incident_id=incident_id,
        )
        with self._lock:
            self.containments.append(containment)
            self.mode = "emergency_containment"
            self.mode_reason = reason
            self.last_heartbeat = now
        audit_event(
            action="phantom.emergency_containment.activate",
            project_slug=project_slug,
            actor=actor,
            provider=provider,
            result="contained",
            details={"scope": scope, "reason": reason, "action_family": action_family, "incident_id": incident_id, "details": details or {}},
        )
        return self.status()

    def recover(self, *, reason: str, actor: str, scope: str = "global", project_slug: Optional[str] = None, provider: Optional[str] = None, action_family: Optional[str] = None, details: Optional[Dict[str, Any]] = None, incident_id: Optional[str] = None) -> Dict[str, Any]:
        released = 0
        with self._lock:
            for containment in self.containments:
                if not containment.active:
                    continue
                if scope != "global" and containment.scope != scope:
                    continue
                if project_slug and containment.project_slug != project_slug:
                    continue
                if provider and containment.provider != provider:
                    continue
                if action_family and containment.action_family != action_family:
                    continue
                containment.active = False
                released += 1
            if not any(c.active for c in self.containments):
                self.mode = "normal"
                self.mode_reason = reason
            self.last_heartbeat = datetime.now(timezone.utc).isoformat()
        audit_event(
            action="phantom.emergency_containment.recover",
            project_slug=project_slug,
            actor=actor,
            provider=provider,
            result="recovered",
            details={"scope": scope, "reason": reason, "released": released, "action_family": action_family, "incident_id": incident_id, "details": details or {}},
        )
        return self.status()

    def gate(self, *, project_slug: str, action: str, actor: str = "unknown", severity: str = SEVERITY_REVERSIBLE_WRITE, resource_type: Optional[str] = None, resource_id: Optional[str] = None, provider: Optional[str] = None, context: Optional[Dict[str, Any]] = None, incident_id: Optional[str] = None) -> Dict[str, Any]:
        context = context or {}
        severity = (severity or SEVERITY_REVERSIBLE_WRITE).strip().lower()
        action = (action or "unknown").strip().lower()
        project_slug = (project_slug or "suite").strip().lower()
        actor = (actor or "unknown").strip()
        event_id = str(uuid.uuid4())
        containment = self._matching_containment(project_slug=project_slug, provider=provider, action=action)
        registered = action in self.irreversible_actions
        dangerous = severity in DANGEROUS_SEVERITIES or registered
        notes: list[str] = []

        with self._lock:
            mode = self.mode

        if mode in {"locked", "degraded", "safe_mode", "emergency_containment"} and dangerous:
            decision = "pause"
            notes.append(f"Dangerous action paused because Phantom Core mode is {mode}.")
        elif containment and dangerous:
            decision = "pause"
            notes.append("Dangerous action paused by active emergency containment scope.")
        elif registered and not context.get("authority_verified"):
            decision = "pause"
            notes.append("Registered irreversible action requires explicit authority_verified context.")
        elif severity == SEVERITY_SOVEREIGNTY_CRITICAL and not context.get("owner_intent_recorded"):
            decision = "pause"
            notes.append("Sovereignty-critical action requires owner_intent_recorded context.")
        else:
            decision = "allow"
            notes.append("Action cleared by current Phantom Core policy.")

        recovery_required = decision in {"pause", "deny"}
        event = {
            "event_id": event_id,
            "decision": decision,
            "mode": mode,
            "project_slug": project_slug,
            "action": action,
            "actor": actor,
            "severity": severity,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "provider": provider,
            "registered_irreversible": registered,
            "dangerous": dangerous,
            "incident_id": incident_id,
            "context_keys": sorted(context.keys()),
            "notes": notes,
        }
        audit_event(
            action="phantom.gate.evaluate",
            project_slug=project_slug,
            actor=actor,
            provider=provider,
            result=decision,
            details=event,
        )
        return {
            "ok": True,
            "decision": decision,
            "mode": mode,
            "action": action,
            "project_slug": project_slug,
            "severity": severity,
            "recovery_required": recovery_required,
            "user_safe_message": USER_SAFE_MESSAGES.get(decision, USER_SAFE_MESSAGES["pause"]),
            "event_id": event_id,
            "notes": notes,
        }

    def events(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list_recent_audit_events(limit=limit, action="phantom.gate.evaluate")

    def _matching_containment(self, *, project_slug: str, provider: Optional[str], action: str) -> Optional[PhantomContainment]:
        action_family = action.split(".")[0] if action else None
        with self._lock:
            containments = list(self.containments)
        for containment in containments:
            if not containment.active:
                continue
            if containment.scope == "global":
                return containment
            if containment.project_slug and containment.project_slug != project_slug:
                continue
            if containment.provider and provider and containment.provider != provider:
                continue
            if containment.action_family and action_family and containment.action_family != action_family:
                continue
            return containment
        return None

    @staticmethod
    def _containment_dict(containment: PhantomContainment) -> Dict[str, Any]:
        return {
            "scope": containment.scope,
            "reason": containment.reason,
            "actor": containment.actor,
            "ts": containment.ts,
            "project_slug": containment.project_slug,
            "provider": containment.provider,
            "action_family": containment.action_family,
            "details": containment.details,
            "incident_id": containment.incident_id,
            "active": containment.active,
        }


phantom_core = PhantomCoreEngine()
