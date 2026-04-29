from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


def _db_path() -> Path:
    raw = os.getenv("ETHER_AUDIT_DB_PATH", "runtime/ether_audit.sqlite3").strip() or "runtime/ether_audit.sqlite3"
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


def init_audit_store() -> None:
    with _connect() as conn:
        conn.execute(
            """
            create table if not exists audit_events (
              id integer primary key autoincrement,
              ts text not null,
              action text not null,
              project_slug text,
              actor text,
              provider text,
              result text not null,
              details_json text not null default '{}'
            )
            """
        )
        conn.execute("create index if not exists audit_events_ts_idx on audit_events (ts desc)")
        conn.execute("create index if not exists audit_events_project_idx on audit_events (project_slug, ts desc)")
        conn.execute("create index if not exists audit_events_action_idx on audit_events (action, ts desc)")
        conn.execute("create index if not exists audit_events_result_idx on audit_events (result, ts desc)")


def persist_audit_event(event: Dict[str, Any]) -> None:
    init_audit_store()
    details = event.get("details") if isinstance(event.get("details"), dict) else {}
    with _connect() as conn:
        conn.execute(
            """
            insert into audit_events (ts, action, project_slug, actor, provider, result, details_json)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.get("ts") or "",
                event.get("action") or "unknown",
                event.get("project_slug"),
                event.get("actor"),
                event.get("provider"),
                event.get("result") or "unknown",
                json.dumps(details, sort_keys=True),
            ),
        )


def _row_to_event(row: sqlite3.Row) -> Dict[str, Any]:
    try:
        details = json.loads(row["details_json"] or "{}")
    except Exception:
        details = {}
    return {
        "id": row["id"],
        "ts": row["ts"],
        "action": row["action"],
        "project_slug": row["project_slug"],
        "actor": row["actor"],
        "provider": row["provider"],
        "result": row["result"],
        "details": details,
    }


def list_persistent_audit_events(
    *,
    limit: int = 100,
    project_slug: Optional[str] = None,
    action: Optional[str] = None,
    result: Optional[str] = None,
) -> List[Dict[str, Any]]:
    init_audit_store()
    clauses: list[str] = []
    params: list[Any] = []
    if project_slug:
        clauses.append("lower(project_slug) = lower(?)")
        params.append(project_slug.strip())
    if action:
        clauses.append("lower(action) = lower(?)")
        params.append(action.strip())
    if result:
        clauses.append("lower(result) = lower(?)")
        params.append(result.strip())

    where = f"where {' and '.join(clauses)}" if clauses else ""
    safe_limit = max(1, min(limit, 500))
    query = f"select * from audit_events {where} order by ts desc, id desc limit ?"
    params.append(safe_limit)
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_event(row) for row in rows]


def persistent_audit_snapshot(limit: int = 100) -> Dict[str, Any]:
    events = list_persistent_audit_events(limit=limit)
    action_counts: Dict[str, int] = {}
    project_counts: Dict[str, int] = {}
    result_counts: Dict[str, int] = {}
    for event in events:
        action_key = event.get("action") or "unknown"
        project_key = event.get("project_slug") or "suite"
        result_key = event.get("result") or "unknown"
        action_counts[action_key] = action_counts.get(action_key, 0) + 1
        project_counts[project_key] = project_counts.get(project_key, 0) + 1
        result_counts[result_key] = result_counts.get(result_key, 0) + 1
    return {
        "storage": "sqlite",
        "db_path_configured": bool(os.getenv("ETHER_AUDIT_DB_PATH", "").strip()),
        "included_events": len(events),
        "action_counts": action_counts,
        "project_counts": project_counts,
        "result_counts": result_counts,
        "recent_events": events,
    }
