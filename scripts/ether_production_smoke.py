from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Tuple

import httpx


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _request(client: httpx.Client, method: str, url: str, headers: Dict[str, str], payload: Dict[str, Any] | None = None) -> Tuple[bool, Dict[str, Any]]:
    try:
        if method == "GET":
            response = client.get(url, headers=headers)
        else:
            response = client.post(url, headers=headers, json=payload or {})
    except Exception as exc:
        return False, {"ok": False, "error": str(exc), "url": url}

    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text[:1000]}
    return response.status_code < 400 and bool(body.get("ok", True)), {
        "status_code": response.status_code,
        "url": url,
        "body": body,
    }


def main() -> None:
    base_url = _env("ETHER_BASE_URL")
    token = _env("ETHER_INTERNAL_TOKEN")
    source = _env("ETHER_SMOKE_SOURCE", "admin")
    timeout_seconds = float(_env("ETHER_SMOKE_TIMEOUT_SECONDS", "45"))

    if not base_url:
        print(json.dumps({"ok": False, "error": "ETHER_BASE_URL is required."}, indent=2))
        raise SystemExit(1)
    if not token:
        print(json.dumps({"ok": False, "error": "ETHER_INTERNAL_TOKEN is required."}, indent=2))
        raise SystemExit(1)

    root = base_url.rstrip("/")
    headers = {
        "X-ETHER-INTERNAL-TOKEN": token,
        "X-ETHER-SOURCE": source,
        "Content-Type": "application/json",
    }

    checks: List[Tuple[str, str, str, Dict[str, Any] | None]] = [
        ("health", "GET", f"{root}/health", None),
        ("version", "GET", f"{root}/version", None),
        ("production_gate_before", "GET", f"{root}/operations/production/gate", None),
        ("suite_status", "GET", f"{root}/operations/suite/status", None),
        ("cron_status", "GET", f"{root}/operations/cron/status", None),
        ("controls_blockers", "GET", f"{root}/controls/blockers", None),
        ("provider_readiness", "GET", f"{root}/providers/readiness/suite", None),
        ("sentinel_status", "GET", f"{root}/sentinel/status", None),
        ("webhook_status", "GET", f"{root}/webhooks/status", None),
        (
            "suite_smoke",
            "POST",
            f"{root}/operations/suite/smoke",
            {
                "project_slugs": ["circa_haus", "exclusivity"],
                "include_unconfigured": False,
                "signal_kind": "production_smoke_test",
                "status": "ok",
                "meta": {"runner": "scripts/ether_production_smoke.py"},
            },
        ),
        (
            "cron_signal",
            "POST",
            f"{root}/operations/cron/signal",
            {
                "project_slugs": ["circa_haus", "exclusivity"],
                "signal_kind": "production_smoke_cron_signal",
                "status": "ok",
                "include_unconfigured": False,
                "meta": {"runner": "scripts/ether_production_smoke.py"},
            },
        ),
        ("signal_health", "GET", f"{root}/operations/signal/health", None),
        ("production_gate_after", "GET", f"{root}/operations/production/gate", None),
    ]

    results: Dict[str, Any] = {}
    overall_ok = True
    with httpx.Client(timeout=timeout_seconds) as client:
        for name, method, url, payload in checks:
            ok, result = _request(client, method, url, headers, payload)
            results[name] = {"ok": ok, **result}
            if name in {"health", "version"}:
                overall_ok = overall_ok and ok
            elif name == "production_gate_after":
                body = result.get("body", {})
                overall_ok = overall_ok and ok and body.get("decision") == "go"

    output = {
        "ok": overall_ok,
        "base_url": root,
        "source": source,
        "decision": results.get("production_gate_after", {}).get("body", {}).get("decision"),
        "blockers": results.get("production_gate_after", {}).get("body", {}).get("blockers"),
        "results": results,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    if not overall_ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
