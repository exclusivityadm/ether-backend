from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Optional


def _db_path() -> Path:
    raw = os.getenv("ETHER_CONTROL_DB_PATH", os.getenv("ETHER_AUDIT_DB_PATH", "runtime/ether_audit.sqlite3")).strip() or "runtime/ether_audit.sqlite3"
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


def init_control_store() -> None:
    with _connect() as conn:
        conn.execute(
            """
            create table if not exists project_controls (
              project_slug text primary key,
              disabled integer not null default 0,
              reason text,
              details_json text not null default '{}',
              updated_at text not null
            )
            """
        )
        conn.execute(
            """
            create table if not exists provider_controls (
              project_slug text not null,
              provider text not null,
              disabled integer not null default 0,
              reason text,
              details_json text not null default '{}',
              updated_at text not null,
              primary key (project_slug, provider)
            )
            """
        )
        conn.execute("create index if not exists provider_controls_project_idx on provider_controls (project_slug)")
        conn.execute("create index if not exists project_controls_disabled_idx on project_controls (disabled)")
        conn.execute("create index if not exists provider_controls_disabled_idx on provider_controls (disabled)")


def save_project_control(*, project_slug: str, disabled: bool, reason: Optional[str], details: Dict[str, Any], updated_at: str) -> None:
    init_control_store()
    with _connect() as conn:
        conn.execute(
            """
            insert into project_controls (project_slug, disabled, reason, details_json, updated_at)
            values (?, ?, ?, ?, ?)
            on conflict(project_slug) do update set
              disabled = excluded.disabled,
              reason = excluded.reason,
              details_json = excluded.details_json,
              updated_at = excluded.updated_at
            """,
            (project_slug.strip().lower(), 1 if disabled else 0, reason, json.dumps(details or {}, sort_keys=True), updated_at),
        )


def save_provider_control(*, project_slug: str, provider: str, disabled: bool, reason: Optional[str], details: Dict[str, Any], updated_at: str) -> None:
    init_control_store()
    with _connect() as conn:
        conn.execute(
            """
            insert into provider_controls (project_slug, provider, disabled, reason, details_json, updated_at)
            values (?, ?, ?, ?, ?, ?)
            on conflict(project_slug, provider) do update set
              disabled = excluded.disabled,
              reason = excluded.reason,
              details_json = excluded.details_json,
              updated_at = excluded.updated_at
            """,
            (project_slug.strip().lower(), provider.strip().lower(), 1 if disabled else 0, reason, json.dumps(details or {}, sort_keys=True), updated_at),
        )


def _details(raw: str) -> Dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def load_control_snapshot() -> Dict[str, Any]:
    init_control_store()
    with _connect() as conn:
        project_rows = conn.execute("select * from project_controls").fetchall()
        provider_rows = conn.execute("select * from provider_controls").fetchall()
    return {
        "projects": {
            row["project_slug"]: {
                "disabled": bool(row["disabled"]),
                "reason": row["reason"],
                "details": _details(row["details_json"]),
                "updated_at": row["updated_at"],
            }
            for row in project_rows
        },
        "providers": {
            f"{row['project_slug']}:{row['provider']}": {
                "project_slug": row["project_slug"],
                "provider": row["provider"],
                "disabled": bool(row["disabled"]),
                "reason": row["reason"],
                "details": _details(row["details_json"]),
                "updated_at": row["updated_at"],
            }
            for row in provider_rows
        },
    }
