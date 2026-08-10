from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(content: str) -> str:
    return hashlib.sha256((content or "").encode("utf-8")).hexdigest()


@dataclass
class WebSource:
    id: str
    project_slug: str
    kind: str
    url: str
    authority: str = "authoritative"
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_checked_at: Optional[str] = None
    last_changed_at: Optional[str] = None
    fingerprint: Optional[str] = None
    observation_count: int = 0


class WebIntelligenceRegistry:
    """Stores only registered sources and compact change state.

    Fetch/browser execution is intentionally separate so hostile web content
    never receives credentials or direct access to Ether's privileged services.
    """

    def __init__(self) -> None:
        self._sources: Dict[str, WebSource] = {}
        self._changes: List[dict] = []

    def register_source(self, source: WebSource) -> WebSource:
        parsed = urlparse(source.url)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            raise ValueError("source URL must be an absolute http(s) URL")
        self._sources[source.id] = source
        return source

    def list_sources(self, project_slug: Optional[str] = None) -> List[dict]:
        rows = self._sources.values()
        if project_slug:
            rows = [row for row in rows if row.project_slug == project_slug]
        return [asdict(row) for row in rows]

    def source(self, source_id: str) -> Optional[WebSource]:
        return self._sources.get(source_id)

    def record_observation(self, source_id: str, content: str, evidence: Optional[Dict[str, Any]] = None) -> dict:
        source = self._sources.get(source_id)
        if source is None:
            raise ValueError("unknown source")
        new_fingerprint = _fingerprint(content)
        previous = source.fingerprint
        changed = previous is not None and previous != new_fingerprint
        first_observation = previous is None
        now = _now_iso()
        source.last_checked_at = now
        source.observation_count += 1
        source.fingerprint = new_fingerprint
        if changed or first_observation:
            source.last_changed_at = now
        result = {
            "source_id": source_id,
            "project_slug": source.project_slug,
            "changed": changed,
            "first_observation": first_observation,
            "fingerprint": new_fingerprint,
            "previous_fingerprint": previous,
            "observed_at": now,
            "evidence": dict(evidence or {}),
        }
        if changed:
            self._changes.append(result)
            self._changes = self._changes[-1000:]
        return result

    def recent_changes(self, project_slug: Optional[str] = None, limit: int = 100) -> List[dict]:
        rows = self._changes
        if project_slug:
            rows = [row for row in rows if row["project_slug"] == project_slug]
        return list(reversed(rows[-max(1, min(limit, 500)):]))

    def choose_execution_path(self, *, requires_javascript: bool, requires_interaction: bool, authenticated: bool) -> str:
        if authenticated or requires_interaction:
            return "isolated_browser"
        if requires_javascript:
            return "lightweight_browser"
        return "http_fetch"


web_intelligence_registry = WebIntelligenceRegistry()
