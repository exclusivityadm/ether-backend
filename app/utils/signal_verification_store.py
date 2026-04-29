from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


def _db_path() -> Path:
    raw = os.getenv("ETHER_SIGNAL_DB_PATH", os.getenv("ETHER_AUDIT_DB_PATH", "runtime/ether_audit.sqlite3")).strip() or "runtime/ether_audit.sqlite3"
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


def init_signal_verification_store() -> None:
    with _connect() as conn:
        conn.execute(
            """
            create table if not exists signal_runs (
              id integer primary key autoincrement,
              project_slug text not null,
              signal_kind text not null,
              lane_id text,
              status text not null,
              write_ok integer not null default 0,
              readback_ok integer not null default 0,
              verified_ok integer not null default 0,
              write_mode text,
              write_target text,
              readback_mode text,
              readback_target text,
              error text,
              write_result_json text not null default '{}',
              readback_result_json text not null default '{}',
              payload_summary_json text not null default '{}',
              recorded_at text not null
            )
            """
        )
        conn.execute("create index if not exists signal_runs_project_recorded_idx on signal_runs (project_slug, recorded_at desc)")
        conn.execute("create index if not exists signal_runs_status_idx on signal_runs (status, recorded_at desc)")
        conn.execute("create index if not exists signal_runs_verified_idx on signal_runs (verified_ok, recorded_at desc)")


def _json(value: Dict[str, Any]) -> str:
    return json.dumps(value or {}, sort_keys=True)


def _details(raw: str) -> Dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def save_signal_run(
    *,
    project_slug: str,
    signal_kind: str,
    lane_id: Optional[str],
    status: str,
    write_ok: bool,
    readback_ok: bool,
    verified_ok: bool,
    write_mode: Optional[str],
    write_target: Optional[str],
    readback_mode: Optional[str],
    readback_target: Optional[str],
    error: Optional[str],
    write_result: Dict[str, Any],
    readback_result: Dict[str, Any],
    payload_summary: Dict[str, Any],
    recorded_at: str,
) -> Dict[str, Any]:
    init_signal_verification_store()
    with _connect() as conn:
        cursor = conn.execute(
            """
            insert into signal_runs (
              project_slug, signal_kind, lane_id, status, write_ok, readback_ok, verified_ok,
              write_mode, write_target, readback_mode, readback_target, error,
              write_result_json, readback_result_json, payload_summary_json, recorded_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_slug.strip().lower(),
                signal_kind,
                lane_id,
                status,
                1 if write_ok else 0,
                1 if readback_ok else 0,
                1 if verified_ok else 0,
                write_mode,
                write_target,
                readback_mode,
                readback_target,
                error,
                _json(write_result),
                _json(readback_result),
                _json(payload_summary),
                recorded_at,
            ),
        )
        row = conn.execute("select * from signal_runs where id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_signal_run(row) if row else {}


def list_signal_runs(
    *,
    project_slug: Optional[str] = None,
    verified_ok: Optional[bool] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    init_signal_verification_store()
    clauses: list[str] = []
    params: list[Any] = []
    if project_slug:
        clauses.append("project_slug = ?")
        params.append(project_slug.strip().lower())
    if verified_ok is not None:
        clauses.append("verified_ok = ?")
        params.append(1 if verified_ok else 0)
    where = f"where {' and '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 500)))
    with _connect() as conn:
        rows = conn.execute(f"select * from signal_runs {where} order by recorded_at desc, id desc limit ?", params).fetchall()
    return [_row_to_signal_run(row) for row in rows]


def signal_verification_snapshot(project_slug: Optional[str] = None) -> Dict[str, Any]:
    runs = list_signal_runs(project_slug=project_slug, limit=200)
    project_counts: Dict[str, int] = {}
    verified_counts: Dict[str, int] = {"ok": 0, "failed": 0}
    status_counts: Dict[str, int] = {}
    last_success_by_project: Dict[str, Dict[str, Any]] = {}
    last_failure_by_project: Dict[str, Dict[str, Any]] = {}

    for run in runs:
        slug = run["project_slug"]
        project_counts[slug] = project_counts.get(slug, 0) + 1
        status_counts[run["status"]] = status_counts.get(run["status"], 0) + 1
        if run["verified_ok"]:
            verified_counts["ok"] += 1
            last_success_by_project.setdefault(slug, run)
        else:
            verified_counts["failed"] += 1
            last_failure_by_project.setdefault(slug, run)

    return {
        "project_slug": project_slug,
        "run_count": len(runs),
        "project_counts": project_counts,
        "verified_counts": verified_counts,
        "status_counts": status_counts,
        "last_success_by_project": last_success_by_project,
        "last_failure_by_project": last_failure_by_project,
        "recent_runs": runs[:25],
    }


def _row_to_signal_run(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "project_slug": row["project_slug"],
        "signal_kind": row["signal_kind"],
        "lane_id": row["lane_id"],
        "status": row["status"],
        "write_ok": bool(row["write_ok"]),
        "readback_ok": bool(row["readback_ok"]),
        "verified_ok": bool(row["verified_ok"]),
        "write_mode": row["write_mode"],
        "write_target": row["write_target"],
        "readback_mode": row["readback_mode"],
        "readback_target": row["readback_target"],
        "error": row["error"],
        "write_result": _details(row["write_result_json"]),
        "readback_result": _details(row["readback_result_json"]),
        "payload_summary": _details(row["payload_summary_json"]),
        "recorded_at": row["recorded_at"],
    }
