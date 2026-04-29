from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


def _db_path() -> Path:
    raw = os.getenv("ETHER_WEBHOOK_DB_PATH", os.getenv("ETHER_AUDIT_DB_PATH", "runtime/ether_audit.sqlite3")).strip() or "runtime/ether_audit.sqlite3"
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


def init_webhook_store() -> None:
    with _connect() as conn:
        conn.execute(
            """
            create table if not exists webhook_events (
              id integer primary key autoincrement,
              event_uid text not null unique,
              project_slug text not null,
              provider text not null,
              event_type text,
              provider_event_id text,
              status text not null,
              accepted integer not null default 0,
              duplicate integer not null default 0,
              payload_hash text not null,
              payload_json text not null default '{}',
              headers_json text not null default '{}',
              validation_json text not null default '{}',
              received_at text not null,
              processed_at text,
              notes text
            )
            """
        )
        conn.execute("create index if not exists webhook_events_project_provider_idx on webhook_events (project_slug, provider, received_at desc)")
        conn.execute("create index if not exists webhook_events_status_idx on webhook_events (status, received_at desc)")
        conn.execute("create index if not exists webhook_events_provider_event_idx on webhook_events (provider, provider_event_id)")
        conn.execute("create index if not exists webhook_events_payload_hash_idx on webhook_events (payload_hash)")


def canonical_payload_hash(payload: Dict[str, Any]) -> str:
    text = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_event_uid(*, project_slug: str, provider: str, provider_event_id: Optional[str], payload_hash: str) -> str:
    base = f"{project_slug.strip().lower()}::{provider.strip().lower()}::{provider_event_id or payload_hash}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _json(value: Dict[str, Any]) -> str:
    return json.dumps(value or {}, sort_keys=True)


def _details(raw: str) -> Dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def event_exists(event_uid: str) -> bool:
    init_webhook_store()
    with _connect() as conn:
        row = conn.execute("select id from webhook_events where event_uid = ?", (event_uid,)).fetchone()
    return row is not None


def save_webhook_event(
    *,
    event_uid: str,
    project_slug: str,
    provider: str,
    event_type: Optional[str],
    provider_event_id: Optional[str],
    status: str,
    accepted: bool,
    duplicate: bool,
    payload_hash: str,
    payload: Dict[str, Any],
    headers: Dict[str, Any],
    validation: Dict[str, Any],
    received_at: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    init_webhook_store()
    with _connect() as conn:
        if event_exists(event_uid):
            row = conn.execute("select * from webhook_events where event_uid = ?", (event_uid,)).fetchone()
            return _row_to_event(row) if row else {}
        cursor = conn.execute(
            """
            insert into webhook_events (
              event_uid, project_slug, provider, event_type, provider_event_id, status,
              accepted, duplicate, payload_hash, payload_json, headers_json, validation_json,
              received_at, notes
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_uid,
                project_slug.strip().lower(),
                provider.strip().lower(),
                event_type,
                provider_event_id,
                status,
                1 if accepted else 0,
                1 if duplicate else 0,
                payload_hash,
                _json(payload),
                _json(headers),
                _json(validation),
                received_at,
                notes,
            ),
        )
        row = conn.execute("select * from webhook_events where id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_event(row) if row else {}


def list_webhook_events(
    *,
    project_slug: Optional[str] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    init_webhook_store()
    clauses: list[str] = []
    params: list[Any] = []
    if project_slug:
        clauses.append("project_slug = ?")
        params.append(project_slug.strip().lower())
    if provider:
        clauses.append("provider = ?")
        params.append(provider.strip().lower())
    if status:
        clauses.append("status = ?")
        params.append(status.strip().lower())
    where = f"where {' and '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 500)))
    with _connect() as conn:
        rows = conn.execute(f"select * from webhook_events {where} order by received_at desc, id desc limit ?", params).fetchall()
    return [_row_to_event(row) for row in rows]


def webhook_snapshot(project_slug: Optional[str] = None) -> Dict[str, Any]:
    events = list_webhook_events(project_slug=project_slug, limit=200)
    status_counts: Dict[str, int] = {}
    provider_counts: Dict[str, int] = {}
    duplicate_count = 0
    accepted_count = 0
    for event in events:
        status_counts[event["status"]] = status_counts.get(event["status"], 0) + 1
        provider_counts[event["provider"]] = provider_counts.get(event["provider"], 0) + 1
        duplicate_count += 1 if event.get("duplicate") else 0
        accepted_count += 1 if event.get("accepted") else 0
    return {
        "project_slug": project_slug,
        "event_count": len(events),
        "accepted_count": accepted_count,
        "duplicate_count": duplicate_count,
        "status_counts": status_counts,
        "provider_counts": provider_counts,
        "recent_events": events[:25],
    }


def _row_to_event(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "event_uid": row["event_uid"],
        "project_slug": row["project_slug"],
        "provider": row["provider"],
        "event_type": row["event_type"],
        "provider_event_id": row["provider_event_id"],
        "status": row["status"],
        "accepted": bool(row["accepted"]),
        "duplicate": bool(row["duplicate"]),
        "payload_hash": row["payload_hash"],
        "payload": _details(row["payload_json"]),
        "headers": _details(row["headers_json"]),
        "validation": _details(row["validation_json"]),
        "received_at": row["received_at"],
        "processed_at": row["processed_at"],
        "notes": row["notes"],
    }
