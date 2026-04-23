# app/utils/sentinel.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


SEVERITY_SCORES = {
    "low": 20,
    "medium": 50,
    "high": 75,
    "critical": 95,
}


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


@dataclass
class QuarantineRecord:
    project_slug: str
    target_type: str
    target_id: str
    reason: str
    status: str = "active"
    expires_at: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class SentinelEngine:
    def __init__(self) -> None:
        self._threats: List[ThreatRecord] = []
        self._quarantines: List[QuarantineRecord] = []

    def score_event(self, severity: str, event_type: str, details: Dict[str, Any]) -> int:
        score = SEVERITY_SCORES.get((severity or "medium").strip().lower(), 50)
        if details.get("replay_detected"):
            score += 10
        if details.get("cross_project_attempt"):
            score += 20
        if details.get("provider_abuse"):
            score += 15
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
        risk_score = self.score_event(severity, event_type, details)
        disposition, quarantined = self.decide_disposition(risk_score)
        record = ThreatRecord(
            project_slug=project_slug,
            event_type=event_type,
            severity=severity,
            risk_score=risk_score,
            disposition=disposition,
            quarantined=quarantined,
            actor_id=actor_id,
            source_ip=source_ip,
            details=details,
        )
        self._threats.append(record)
        if quarantined and actor_id:
            self._quarantines.append(
                QuarantineRecord(
                    project_slug=project_slug,
                    target_type="actor",
                    target_id=actor_id,
                    reason=f"Auto-quarantined due to {event_type}",
                    details={"risk_score": risk_score, **details},
                )
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
        record = QuarantineRecord(
            project_slug=project_slug,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            expires_at=expires_at,
            details=details,
        )
        self._quarantines.append(record)
        return record

    def list_threats(self, project_slug: Optional[str] = None, limit: Optional[int] = None) -> List[ThreatRecord]:
        if not project_slug:
            items = list(self._threats)
        else:
            items = [t for t in self._threats if t.project_slug == project_slug]
        if limit is not None:
            return items[-limit:]
        return items

    def list_quarantines(self, project_slug: Optional[str] = None) -> List[QuarantineRecord]:
        if not project_slug:
            return list(self._quarantines)
        return [q for q in self._quarantines if q.project_slug == project_slug]


sentinel_engine = SentinelEngine()
