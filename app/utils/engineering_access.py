from __future__ import annotations

import hashlib
import secrets
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class EngineeringSession:
    session_id: str
    principal: str
    project_slug: str
    capabilities: List[str]
    issued_at: str
    expires_at: str
    source: Optional[str] = None
    consumed: bool = False
    revoked: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


class EngineeringAccessBroker:
    """Short-lived internal engineering sessions.

    Raw bearer material is never stored. Tickets are one-use bootstrap tokens;
    exchanged sessions are short-lived and capability-scoped. This broker is
    intentionally separate from normal app/user authentication.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tickets: Dict[str, EngineeringSession] = {}
        self._sessions: Dict[str, EngineeringSession] = {}

    def issue_ticket(
        self,
        *,
        principal: str,
        project_slug: str,
        capabilities: List[str],
        source: Optional[str] = None,
        ttl_seconds: int = 180,
        metadata: Optional[Dict[str, str]] = None,
    ) -> dict:
        ttl = max(30, min(int(ttl_seconds), 600))
        now = _utc_now()
        expires = now + timedelta(seconds=ttl)
        ticket = secrets.token_urlsafe(32)
        ticket_hash = _hash_token(ticket)
        record = EngineeringSession(
            session_id=f"eng_{secrets.token_hex(12)}",
            principal=principal.strip() or "internal-engineer",
            project_slug=project_slug.strip().lower(),
            capabilities=sorted(set(capabilities)),
            source=source,
            issued_at=_iso(now),
            expires_at=_iso(expires),
            metadata=dict(metadata or {}),
        )
        with self._lock:
            self._tickets[ticket_hash] = record
        return {"ticket": ticket, "session": asdict(record)}

    def exchange_ticket(self, ticket: str) -> Optional[dict]:
        ticket_hash = _hash_token(ticket.strip())
        with self._lock:
            record = self._tickets.get(ticket_hash)
            if record is None or record.consumed or record.revoked:
                return None
            if datetime.fromisoformat(record.expires_at) <= _utc_now():
                record.revoked = True
                return None
            record.consumed = True
            bearer = secrets.token_urlsafe(40)
            bearer_hash = _hash_token(bearer)
            # Browser session is deliberately short-lived; ticket expiry is the ceiling.
            now = _utc_now()
            ticket_expiry = datetime.fromisoformat(record.expires_at)
            session_expiry = min(ticket_expiry, now + timedelta(minutes=10))
            session = EngineeringSession(
                session_id=record.session_id,
                principal=record.principal,
                project_slug=record.project_slug,
                capabilities=list(record.capabilities),
                source=record.source,
                issued_at=_iso(now),
                expires_at=_iso(session_expiry),
                metadata=dict(record.metadata),
            )
            self._sessions[bearer_hash] = session
            return {"bearer": bearer, "session": asdict(session)}

    def verify(self, bearer: str, capability: Optional[str] = None) -> Optional[EngineeringSession]:
        bearer_hash = _hash_token(bearer.strip())
        with self._lock:
            record = self._sessions.get(bearer_hash)
            if record is None or record.revoked:
                return None
            if datetime.fromisoformat(record.expires_at) <= _utc_now():
                record.revoked = True
                return None
            if capability and capability not in record.capabilities:
                return None
            return record

    def revoke(self, session_id: str) -> int:
        count = 0
        with self._lock:
            for record in list(self._tickets.values()) + list(self._sessions.values()):
                if record.session_id == session_id and not record.revoked:
                    record.revoked = True
                    count += 1
        return count

    def list_sessions(self) -> list[dict]:
        with self._lock:
            return [asdict(record) for record in self._sessions.values()]


engineering_access_broker = EngineeringAccessBroker()
