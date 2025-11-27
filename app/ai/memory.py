import os
import sqlite3
from contextlib import contextmanager
from typing import Optional

from sqlalchemy.orm import Session

from app.models.memory import UnifyMemory


SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ether_memory_cache.db")


@contextmanager
def sqlite_conn():
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS memory_cache ("
            "key TEXT PRIMARY KEY,"
            "value TEXT,"
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        yield conn
        conn.commit()
    finally:
        conn.close()


def _build_scope(
    persona: str,
    merchant_id: Optional[int],
    customer_id: Optional[int],
    app_context: Optional[str],
) -> str:
    return f"{persona or 'global'}|{merchant_id or 0}|{customer_id or 0}|{app_context or 'any'}"


def store_memory(
    db: Session,
    persona: str,
    merchant_id: Optional[int],
    customer_id: Optional[int],
    app_context: Optional[str],
    key: str,
    value: str,
) -> None:
    """Store memory in Supabase Postgres (primary) with SQLite as fallback."""
    scope = _build_scope(persona, merchant_id, customer_id, app_context)

    try:
        record = UnifyMemory(scope=scope, key=key, value=value)
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()
        # Fallback to local SQLite cache
        with sqlite_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO memory_cache (key, value) VALUES (?, ?)",
                (f"{scope}:{key}", value),
            )


def load_memory(
    db: Session,
    persona: str,
    merchant_id: Optional[int],
    customer_id: Optional[int],
    app_context: Optional[str],
    key: str,
) -> Optional[str]:
    scope = _build_scope(persona, merchant_id, customer_id, app_context)

    # First try Postgres
    try:
        record = (
            db.query(UnifyMemory)
            .filter(UnifyMemory.scope == scope, UnifyMemory.key == key)
            .order_by(UnifyMemory.created_at.desc())
            .first()
        )
        if record:
            return record.value
    except Exception:
        # If Postgres is down, fall back to SQLite
        pass

    try:
        with sqlite_conn() as conn:
            cur = conn.execute(
                "SELECT value FROM memory_cache WHERE key = ?",
                (f"{scope}:{key}",),
            )
            row = cur.fetchone()
            if row:
                return row[0]
    except Exception:
        return None

    return None
