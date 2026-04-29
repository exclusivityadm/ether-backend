from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


def _db_path() -> Path:
    raw = os.getenv("ETHER_SENTINEL_DB_PATH", os.getenv("ETHER_AUDIT_DB_PATH", "runtime/ether_audit.sqlite3")).strip() or "runtime/ether_audit.sqlite3"
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_sentinel_store() -> None:
    with _connect() as conn:
        conn.execute(
            """
            create table if not exists sentinel_threats (
              id integer primary key autoincrement,
              project_slug text not null,
              event_type text not null,
              severity text not null,
              risk_score integer not null,
              disposition text not null,
              quarantined integer not null default 0,
              actor_id text,
              source_ip text,
              status text not null default 'open',
              details_json text not null default '{}',
              created_at text not null,
              reviewed_at text,
              reviewer text,
              review_notes text
            )
            """
        )
        conn.execute(
            """
            create table if not exists sentinel_quarantines (
              id integer primary key autoincrement,
              project_slug text not null,
              target_type text not null,
              target_id text not null,
              reason text not null,
              status text not null default 'active',
              expires_at text,
              details_json text not null default '{}',
              created_at text not null,
              released_at text,
              released_by text,
              release_reason text
            )
            """
        )
        conn.execute("create index if not exists sentinel_threats_project_created_idx on sentinel_threats (project_slug, created_at desc)")
        conn.execute("create index if not exists sentinel_threats_status_idx on sentinel_threats (status, created_at desc)")
        conn.execute("create index if not exists sentinel_threats_disposition_idx on sentinel_threats (disposition, created_at desc)")
        conn.execute("create index if not exists sentinel_quarantines_project_status_idx on sentinel_quarantines (project_slug, status)")
        conn.execute("create index if not exists sentinel_quarantines_target_idx on sentinel_quarantines (target_type, target_id)")


def _json(value: Dict[str, Any]) -> str:
    return json.dumps(value or {}, sort_keys=True)


def _details(raw: str) -> Dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def save_threat(
    *,
    project_slug: str,
    event_type: str,
    severity: str,
    risk_score: int,
    disposition: str,
    quarantined: bool,
    actor_id: Optional[str],
    source_ip: Optional[str],
    details: Dict[str, Any],
    created_at: str,
) -> int:
    init_sentinel_store()
    with _connect() as conn:
        cursor = conn.execute(
            """
            insert into sentinel_threats (
              project_slug, event_type, severity, risk_score, disposition, quarantined,
              actor_id, source_ip, status, details_json, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_slug,
                event_type,
                severity,
                risk_score,
                disposition,
                1 if quarantined else 0,
                actor_id,
                source_ip,
                "open" if disposition in {"review", "quarantine"} else "observed",
                _json(details),
                created_at,
            ),
        )
        return int(cursor.lastrowid)


def save_quarantine(
    *,
    project_slug: str,
    target_type: str,
    target_id: str,
    reason: str,
    status: str,
    expires_at: Optional[str],
    details: Dict[str, Any],
    created_at: str,
) -> int:
    init_sentinel_store()
    with _connect() as conn:
        cursor = conn.execute(
            """
            insert into sentinel_quarantines (
              project_slug, target_type, target_id, reason, status, expires_at, details_json, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_slug, target_type, target_id, reason, status, expires_at, _json(details), created_at),
        )
        return int(cursor.lastrowid)


def list_threat_rows(project_slug: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    init_sentinel_store()
    clauses: list[str] = []
    params: list[Any] = []
    if project_slug:
        clauses.append("project_slug = ?")
        params.append(project_slug.strip().lower())
    if status:
        clauses.append("status = ?")
        params.append(status.strip().lower())
    where = f"where {' and '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 500)))
    with _connect() as conn:
        rows = conn.execute(f"select * from sentinel_threats {where} order by created_at desc, id desc limit ?", params).fetchall()
    return [_threat_row(row) for row in rows]


def list_quarantine_rows(project_slug: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    init_sentinel_store()
    clauses: list[str] = []
    params: list[Any] = []
    if project_slug:
        clauses.append("project_slug = ?")
        params.append(project_slug.strip().lower())
    if status:
        clauses.append("status = ?")
        params.append(status.strip().lower())
    where = f"where {' and '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 500)))
    with _connect() as conn:
        rows = conn.execute(f"select * from sentinel_quarantines {where} order by created_at desc, id desc limit ?", params).fetchall()
    return [_quarantine_row(row) for row in rows]


def mark_threat_reviewed(*, threat_id: int, reviewer: Optional[str], status: str, review_notes: Optional[str], reviewed_at: str) -> Optional[Dict[str, Any]]:
    init_sentinel_store()
    with _connect() as conn:
        conn.execute(
            """
            update sentinel_threats
            set status = ?, reviewer = ?, review_notes = ?, reviewed_at = ?
            where id = ?
            """,
            (status, reviewer, review_notes, reviewed_at, threat_id),
        )
        row = conn.execute("select * from sentinel_threats where id = ?", (threat_id,)).fetchone()
    return _threat_row(row) if row else None


def release_quarantine(*, quarantine_id: int, released_by: Optional[str], release_reason: str, released_at: str) -> Optional[Dict[str, Any]]:
    init_sentinel_store()
    with _connect() as conn:
        conn.execute(
            """
            update sentinel_quarantines
            set status = 'released', released_by = ?, release_reason = ?, released_at = ?
            where id = ?
            """,
            (released_by, release_reason, released_at, quarantine_id),
        )
        row = conn.execute("select * from sentinel_quarantines where id = ?", (quarantine_id,)).fetchone()
    return _quarantine_row(row) if row else None


def sentinel_snapshot(project_slug: Optional[str] = None) -> Dict[str, Any]:
    threats = list_threat_rows(project_slug=project_slug, limit=100)
    quarantines = list_quarantine_rows(project_slug=project_slug, limit=100)
    threat_status_counts: Dict[str, int] = {}
    disposition_counts: Dict[str, int] = {}
    for threat in threats:
        threat_status_counts[threat["status"]] = threat_status_counts.get(threat["status"], 0) + 1
        disposition_counts[threat["disposition"]] = disposition_counts.get(threat["disposition"], 0) + 1
    quarantine_status_counts: Dict[str, int] = {}
    for quarantine in quarantines:
        quarantine_status_counts[quarantine["status"]] = quarantine_status_counts.get(quarantine["status"], 0) + 1
    return {
        "project_slug": project_slug,
        "threat_count": len(threats),
        "quarantine_count": len(quarantines),
        "threat_status_counts": threat_status_counts,
        "disposition_counts": disposition_counts,
        "quarantine_status_counts": quarantine_status_counts,
        "recent_threats": threats[:20],
        "recent_quarantines": quarantines[:20],
    }


def _threat_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "project_slug": row["project_slug"],
        "event_type": row["event_type"],
        "severity": row["severity"],
        "risk_score": row["risk_score"],
        "disposition": row["disposition"],
        "quarantined": bool(row["quarantined"]),
        "actor_id": row["actor_id"],
        "source_ip": row["source_ip"],
        "status": row["status"],
        "details": _details(row["details_json"]),
        "created_at": row["created_at"],
        "reviewed_at": row["reviewed_at"],
        "reviewer": row["reviewer"],
        "review_notes": row["review_notes"],
    }


def _quarantine_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "project_slug": row["project_slug"],
        "target_type": row["target_type"],
        "target_id": row["target_id"],
        "reason": row["reason"],
        "status": row["status"],
        "expires_at": row["expires_at"],
        "details": _details(row["details_json"]),
        "created_at": row["created_at"],
        "released_at": row["released_at"],
        "released_by": row["released_by"],
        "release_reason": row["release_reason"],
    }
