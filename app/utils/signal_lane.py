from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str) -> str:
    safe = []
    for ch in (value or "").strip().lower():
        if ch.isalnum() or ch in {"_", "-", ":"}:
            safe.append(ch)
        elif ch in {" ", ".", "/"}:
            safe.append("-")
    return "".join(safe) or "unknown"


@dataclass
class SignalLaneRecord:
    project_slug: str
    lane_id: str
    app_id: Optional[str] = None
    instance_id: Optional[str] = None
    domain: Optional[str] = None
    verified: bool = False
    verification_mode: str = "pending-secret"
    proof_required: bool = False
    accepted: bool = True
    server_nonce: str = field(default_factory=lambda: secrets.token_hex(16))
    handshake_count: int = 0
    heartbeat_count: int = 0
    last_status: str = "bootstrapped"
    issued_at: str = field(default_factory=_utc_now_iso)
    last_seen_at: str = field(default_factory=_utc_now_iso)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalHeartbeatResult:
    record: SignalLaneRecord
    accepted: bool
    verified: bool
    verification_mode: str
    proof_required: bool
    keepalive_recorded: bool


class SignalLaneRegistry:
    def __init__(self) -> None:
        self._lanes: Dict[Tuple[str, str], SignalLaneRecord] = {}

    def _lane_key(self, project_slug: str, lane_id: str) -> Tuple[str, str]:
        return (project_slug.strip().lower(), lane_id.strip().lower())

    def _build_lane_id(self, project_slug: str, app_id: Optional[str], instance_id: Optional[str]) -> str:
        return f"{_slugify(project_slug)}:{_slugify(app_id or 'app')}:{_slugify(instance_id or 'instance')}"

    def _proof_material(
        self,
        project_slug: str,
        lane_id: str,
        app_id: Optional[str],
        instance_id: Optional[str],
        client_nonce: Optional[str],
        server_nonce: Optional[str],
    ) -> str:
        return "|".join(
            [
                project_slug.strip().lower(),
                lane_id.strip().lower(),
                (app_id or "").strip().lower(),
                (instance_id or "").strip().lower(),
                (server_nonce or "").strip(),
                (client_nonce or "").strip(),
            ]
        )

    def _proof_matches(
        self,
        secret: str,
        project_slug: str,
        lane_id: str,
        app_id: Optional[str],
        instance_id: Optional[str],
        client_nonce: Optional[str],
        presented_proof: Optional[str],
        server_nonce: Optional[str],
    ) -> bool:
        if not secret or not client_nonce or not presented_proof:
            return False
        material = self._proof_material(
            project_slug=project_slug,
            lane_id=lane_id,
            app_id=app_id,
            instance_id=instance_id,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )
        expected = hmac.new(secret.encode("utf-8"), material.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, presented_proof.strip().lower())

    def handshake(
        self,
        *,
        project_slug: str,
        app_id: Optional[str],
        instance_id: Optional[str],
        domain: Optional[str],
        lane_id: Optional[str],
        signal_secret: Optional[str],
        client_nonce: Optional[str],
        presented_proof: Optional[str],
        requested_capabilities: Optional[list[str]] = None,
    ) -> SignalLaneRecord:
        resolved_lane_id = (lane_id or "").strip() or self._build_lane_id(project_slug, app_id, instance_id)
        key = self._lane_key(project_slug, resolved_lane_id)
        existing = self._lanes.get(key)
        server_nonce = existing.server_nonce if existing else None

        proof_required = bool(signal_secret)
        verified = False
        verification_mode = "pending-secret"
        accepted = True

        if proof_required:
            verified = self._proof_matches(
                secret=signal_secret or "",
                project_slug=project_slug,
                lane_id=resolved_lane_id,
                app_id=app_id,
                instance_id=instance_id,
                client_nonce=client_nonce,
                presented_proof=presented_proof,
                server_nonce=server_nonce,
            )
            accepted = verified
            if verified:
                verification_mode = "proof-verified"
            elif presented_proof:
                verification_mode = "proof-mismatch"
            else:
                verification_mode = "proof-required"
        else:
            verified = True
            verification_mode = "pending-secret"
            accepted = True

        record = existing or SignalLaneRecord(
            project_slug=project_slug,
            lane_id=resolved_lane_id,
            app_id=app_id,
            instance_id=instance_id,
            domain=domain,
        )
        record.app_id = app_id or record.app_id
        record.instance_id = instance_id or record.instance_id
        record.domain = domain or record.domain
        record.verified = verified
        record.verification_mode = verification_mode
        record.proof_required = proof_required
        record.accepted = accepted
        record.handshake_count += 1
        record.last_status = "verified" if accepted else "awaiting-proof"
        record.last_seen_at = _utc_now_iso()
        record.server_nonce = secrets.token_hex(16)
        record.details = {
            "requested_capabilities": list(requested_capabilities or []),
            "client_nonce_present": bool(client_nonce),
            "proof_present": bool(presented_proof),
        }
        self._lanes[key] = record
        return record

    def heartbeat(
        self,
        *,
        project_slug: str,
        lane_id: str,
        app_id: Optional[str],
        instance_id: Optional[str],
        status: str,
        signal_secret: Optional[str],
        client_nonce: Optional[str],
        presented_proof: Optional[str],
        meta: Optional[Dict[str, Any]] = None,
    ) -> Optional[SignalHeartbeatResult]:
        key = self._lane_key(project_slug, lane_id)
        record = self._lanes.get(key)
        if record is None:
            return None

        proof_required = bool(signal_secret)
        verified_now = False
        accepted = True
        verification_mode = record.verification_mode

        if proof_required and not record.verified:
            verified_now = self._proof_matches(
                secret=signal_secret or "",
                project_slug=project_slug,
                lane_id=lane_id,
                app_id=app_id or record.app_id,
                instance_id=instance_id or record.instance_id,
                client_nonce=client_nonce,
                presented_proof=presented_proof,
                server_nonce=record.server_nonce,
            )
            accepted = verified_now
            if verified_now:
                verification_mode = "proof-verified"
            elif presented_proof:
                verification_mode = "proof-mismatch"
            else:
                verification_mode = "proof-required"
        elif proof_required and record.verified:
            accepted = True
            verification_mode = "proof-verified"
        else:
            accepted = True
            verification_mode = "pending-secret"

        keepalive_recorded = bool(accepted)
        if accepted:
            record.verified = record.verified or verified_now or (not proof_required)
            record.heartbeat_count += 1
            record.last_status = status.strip() or "ok"
            record.last_seen_at = _utc_now_iso()
            record.server_nonce = secrets.token_hex(16)
            record.details = {
                **record.details,
                **(meta or {}),
                "client_nonce_present": bool(client_nonce),
                "proof_present": bool(presented_proof),
            }
        record.proof_required = proof_required
        record.accepted = accepted
        record.verification_mode = verification_mode
        return SignalHeartbeatResult(
            record=record,
            accepted=accepted,
            verified=record.verified,
            verification_mode=verification_mode,
            proof_required=proof_required,
            keepalive_recorded=keepalive_recorded,
        )

    def list_lanes(self, project_slug: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
        rows = []
        for record in self._lanes.values():
            if project_slug and record.project_slug != project_slug:
                continue
            rows.append(asdict(record))
        rows.sort(key=lambda item: item["last_seen_at"], reverse=True)
        return rows[:limit]


signal_lane_registry = SignalLaneRegistry()
