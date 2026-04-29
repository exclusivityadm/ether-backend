from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

import httpx


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _fail(message: str, code: int = 1) -> None:
    print(json.dumps({"ok": False, "error": message}, indent=2))
    raise SystemExit(code)


def main() -> None:
    base_url = _env("ETHER_BASE_URL")
    token = _env("ETHER_INTERNAL_TOKEN")
    source = _env("ETHER_CRON_SOURCE", "admin")
    project_slugs = [item.strip() for item in _env("ETHER_CRON_PROJECTS", "circa_haus,exclusivity").split(",") if item.strip()]
    timeout_seconds = float(_env("ETHER_CRON_TIMEOUT_SECONDS", "30"))

    if not base_url:
        _fail("ETHER_BASE_URL is required.")
    if not token:
        _fail("ETHER_INTERNAL_TOKEN is required.")
    if not project_slugs:
        _fail("ETHER_CRON_PROJECTS produced no project slugs.")

    url = f"{base_url.rstrip('/')}/operations/cron/signal"
    headers = {
        "X-ETHER-INTERNAL-TOKEN": token,
        "X-ETHER-SOURCE": source,
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "project_slugs": project_slugs,
        "signal_kind": "render_cron_keepalive",
        "status": "ok",
        "include_unconfigured": False,
        "meta": {
            "runner": "scripts/ether_cron_signal.py",
            "source": source,
        },
    }

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)
    except Exception as exc:
        _fail(f"Ether cron signal request failed: {exc}")

    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text[:500]}

    output = {
        "ok": response.status_code < 400 and bool(body.get("ok")),
        "status_code": response.status_code,
        "url": url,
        "source": source,
        "projects": project_slugs,
        "response": body,
    }
    print(json.dumps(output, indent=2, sort_keys=True))

    if not output["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
