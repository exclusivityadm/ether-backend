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
    generation: int = 0
    handshake_count: int = 0
    heartbeat_count: int = 0
    last_proof_digest: Optional[str] = None
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
    """In-memory lane registry implementing an evolving challenge-response ratchet.

    A configured lane must prove every authenticated transition.  Successful
    verification rotates the server nonce and increments the generation before
    the next interaction, preventing a previously observed proof from becoming
    a reusable bearer credential.
    """

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
        generation: int,
    ) -> str:
        return "|".join(
            [
                "ether-ratchet-v1",
                project_slug.strip().lower(),
                lane_id.strip().lower(),
                (app_id or "").strip().lower(),
                (instance_id or "").strip().lower(),
                str(generation),
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
        generation: int,
        last_proof_digest: Optional[str],
    ) -> tuple[bool, Optional[str], str]:
        if not secret or not client_nonce or not presented_proof or not server_nonce:
            return False, None, "proof-required"
        material = self._proof_material(
            project_slug=project_slug,
            lane_id=lane_id,
            app_id=app_id,
            instance_id=instance_id,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
            generation=generation,
        )
        expected = hmac.new(secret.encode("utf-8"), material.encode("utf-8"), hashlib.sha256).hexdigest()
        normalized = presented_proof.strip().lower()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if last_proof_digest and hmac.compare_digest(last_proof_digest, digest):
            return False, digest, "replay-rejected"
        matched = hmac.compare_digest(expected, normalized)
        return matched, digest, "proof-verified" if matched else "proof-mismatch"

    def _advance(self, record: SignalLaneRecord, proof_digest: Optional[str]) -> None:
        record.last_proof_digest = proof_digest
        record.generation += 1
        record.server_nonce = secrets.token_hex(16)

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

        proof_required = bool(signal_secret)
        verified = False
        accepted = True
        mode = "pending-secret"
        proof_digest: Optional[str] = None

        if proof_required:
            verified, proof_digest, mode = self._proof_matches(
                secret=signal_secret or "",
                project_slug=project_slug,
                lane_id=resolved_lane_id,
                app_id=record.app_id,
                instance_id=record.instance_id,
                client_nonce=client_nonce,
                presented_proof=presented_proof,
                server_nonce=record.server_nonce,
                generation=record.generation,
                last_proof_digest=record.last_proof_digest,
            )
            accepted = verified
        else:
            verified = True

        record.verified = verified
        record.verification_mode = mode
        record.proof_required = proof_required
        record.accepted = accepted
        record.handshake_count += 1
        record.last_status = "verified" if accepted else "awaiting-proof"
        record.last_seen_at = _utc_now_iso()
        record.details = {
            "requested_capabilities": list(requested_capabilities or []),
            "client_nonce_present": bool(client_nonce),
            "proof_present": bool(presented_proof),
            "ratchet_generation": record.generation,
        }
        if accepted and proof_required:
            self._advance(record, proof_digest)
            record.details["ratchet_generation"] = record.generation
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
        verified_now = True
        accepted = True
        mode = "pending-secret"
        proof_digest: Optional[str] = None

        if proof_required:
            verified_now, proof_digest, mode = self._proof_matches(
                secret=signal_secret or "",
                project_slug=project_slug,
                lane_id=lane_id,
                app_id=app_id or record.app_id,
                instance_id=instance_id or record.instance_id,
                client_nonce=client_nonce,
                presented_proof=presented_proof,
                server_nonce=record.server_nonce,
                generation=record.generation,
                last_proof_digest=record.last_proof_digest,
            )
            accepted = verified_now

        keepalive_recorded = bool(accepted)
        if accepted:
            record.verified = True
            record.heartbeat_count += 1
            record.last_status = status.strip() or "ok"
            record.last_seen_at = _utc_now_iso()
            record.details = {
                **record.details,
                **(meta or {}),
                "client_nonce_present": bool(client_nonce),
                "proof_present": bool(presented_proof),
            }
            if proof_required:
                self._advance(record, proof_digest)
            record.details["ratchet_generation"] = record.generation
        else:
            record.verified = False

        record.proof_required = proof_required
        record.accepted = accepted
        record.verification_mode = mode
        return SignalHeartbeatResult(
            record=record,
            accepted=accepted,
            verified=record.verified,
            verification_mode=mode,
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
