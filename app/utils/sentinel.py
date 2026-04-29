# app/utils/sentinel.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.utils.sentinel_store import (
    init_sentinel_store,
    list_quarantine_rows,
    list_threat_rows,
    mark_threat_reviewed,
    release_quarantine,
    save_quarantine,
    save_threat,
    sentinel_snapshot,
)


SEVERITY_SCORES = {
    "low": 20,
    "medium": 50,
    "high": 75,
    "critical": 95,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ThreatRecord:
    project_slug: str
    event_type: str
    severity: str
    risk_score: int
    disposition: str
    quarantined: bool
    actor_id: Optional[str] = None
    source_ip: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None
    status: str = "open"
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewer: Optional[str] = None
    review_notes: Optional[str] = None


@dataclass
class QuarantineRecord:
    project_slug: str
    target_type: str
    target_id: str
    reason: str
    status: str = "active"
    expires_at: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None
    created_at: Optional[str] = None
    released_at: Optional[str] = None
    released_by: Optional[str] = None
    release_reason: Optional[str] = None


def _threat_from_row(row: Dict[str, Any]) -> ThreatRecord:
    return ThreatRecord(
        id=row.get("id"),
        project_slug=row.get("project_slug") or "",
        event_type=row.get("event_type") or "unknown",
        severity=row.get("severity") or "medium",
        risk_score=int(row.get("risk_score") or 0),
        disposition=row.get("disposition") or "allow",
        quarantined=bool(row.get("quarantined")),
        actor_id=row.get("actor_id"),
        source_ip=row.get("source_ip"),
        details=row.get("details") or {},
        status=row.get("status") or "open",
        created_at=row.get("created_at"),
        reviewed_at=row.get("reviewed_at"),
        reviewer=row.get("reviewer"),
        review_notes=row.get("review_notes"),
    )


def _quarantine_from_row(row: Dict[str, Any]) -> QuarantineRecord:
    return QuarantineRecord(
        id=row.get("id"),
        project_slug=row.get("project_slug") or "",
        target_type=row.get("target_type") or "unknown",
        target_id=row.get("target_id") or "unknown",
        reason=row.get("reason") or "No reason recorded.",
        status=row.get("status") or "active",
        expires_at=row.get("expires_at"),
        details=row.get("details") or {},
        created_at=row.get("created_at"),
        released_at=row.get("released_at"),
        released_by=row.get("released_by"),
        release_reason=row.get("release_reason"),
    )


class SentinelEngine:
    def __init__(self) -> None:
        self._threats: List[ThreatRecord] = []
        self._quarantines: List[QuarantineRecord] = []
        self._initialized = False

    def initialize(self) -> None:
        init_sentinel_store()
        self._threats = [_threat_from_row(row) for row in list_threat_rows(limit=300)]
        self._quarantines = [_quarantine_from_row(row) for row in list_quarantine_rows(limit=300)]
        self._initialized = True

    def score_event(self, severity: str, event_type: str, details: Dict[str, Any]) -> int:
        score = SEVERITY_SCORES.get((severity or "medium").strip().lower(), 50)
        if details.get("replay_detected"):
            score += 10
        if details.get("cross_project_attempt"):
            score += 20
        if details.get("provider_abuse"):
            score += 15
        if details.get("credential_exposure"):
            score += 25
        if details.get("payment_abuse"):
            score += 20
        if details.get("qr_abuse"):
            score += 10
        if "auth" in (event_type or "").lower():
            score += 5
        return max(0, min(score, 100))

    def decide_disposition(self, risk_score: int) -> tuple[str, bool]:
        if risk_score >= 90:
            return "quarantine", True
        if risk_score >= 70:
            return "review", False
        return "allow", False

    def record_threat(
        self,
        *,
        project_slug: str,
        event_type: str,
        severity: str,
        actor_id: Optional[str],
        source_ip: Optional[str],
        details: Dict[str, Any],
    ) -> ThreatRecord:
        slug = project_slug.strip().lower()
        risk_score = self.score_event(severity, event_type, details)
        disposition, quarantined = self.decide_disposition(risk_score)
        created_at = _now()
        record = ThreatRecord(
            project_slug=slug,
            event_type=event_type,
            severity=severity,
            risk_score=risk_score,
            disposition=disposition,
            quarantined=quarantined,
            actor_id=actor_id,
            source_ip=source_ip,
            details=details,
            status="open" if disposition in {"review", "quarantine"} else "observed",
            created_at=created_at,
        )
        record.id = save_threat(
            project_slug=record.project_slug,
            event_type=record.event_type,
            severity=record.severity,
            risk_score=record.risk_score,
            disposition=record.disposition,
            quarantined=record.quarantined,
            actor_id=record.actor_id,
            source_ip=record.source_ip,
            details=record.details,
            created_at=created_at,
        )
        self._threats.append(record)
        self._threats = self._threats[-300:]
        if quarantined and actor_id:
            self.add_quarantine(
                project_slug=slug,
                target_type="actor",
                target_id=actor_id,
                reason=f"Auto-quarantined due to {event_type}",
                expires_at=None,
                details={"risk_score": risk_score, **details},
            )
        return record

    def add_quarantine(
        self,
        *,
        project_slug: str,
        target_type: str,
        target_id: str,
        reason: str,
        expires_at: Optional[str],
        details: Dict[str, Any],
    ) -> QuarantineRecord:
        slug = project_slug.strip().lower()
        created_at = _now()
        record = QuarantineRecord(
            project_slug=slug,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            expires_at=expires_at,
            details=details,
            status="active",
            created_at=created_at,
        )
        record.id = save_quarantine(
            project_slug=record.project_slug,
            target_type=record.target_type,
            target_id=record.target_id,
            reason=record.reason,
            status=record.status,
            expires_at=record.expires_at,
            details=record.details,
            created_at=created_at,
        )
        self._quarantines.append(record)
        self._quarantines = self._quarantines[-300:]
        return record

    def review_threat(self, *, threat_id: int, reviewer: Optional[str], status: str, review_notes: Optional[str]) -> Optional[ThreatRecord]:
        row = mark_threat_reviewed(
            threat_id=threat_id,
            reviewer=reviewer,
            status=status.strip().lower() or "reviewed",
            review_notes=review_notes,
            reviewed_at=_now(),
        )
        if row is None:
            return None
        record = _threat_from_row(row)
        self._threats = [record if item.id == record.id else item for item in self._threats]
        return record

    def release_quarantine(self, *, quarantine_id: int, released_by: Optional[str], release_reason: str) -> Optional[QuarantineRecord]:
        row = release_quarantine(
            quarantine_id=quarantine_id,
            released_by=released_by,
            release_reason=release_reason,
            released_at=_now(),
        )
        if row is None:
            return None
        record = _quarantine_from_row(row)
        self._quarantines = [record if item.id == record.id else item for item in self._quarantines]
        return record

    def list_threats(self, project_slug: Optional[str] = None, limit: Optional[int] = None, status: Optional[str] = None) -> List[ThreatRecord]:
        rows = list_threat_rows(project_slug=project_slug, status=status, limit=limit or 100)
        return [_threat_from_row(row) for row in rows]

    def list_quarantines(self, project_slug: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[QuarantineRecord]:
        rows = list_quarantine_rows(project_slug=project_slug, status=status, limit=limit)
        return [_quarantine_from_row(row) for row in rows]

    def snapshot(self, project_slug: Optional[str] = None) -> Dict[str, Any]:
        return sentinel_snapshot(project_slug=project_slug)


sentinel_engine = SentinelEngine()
