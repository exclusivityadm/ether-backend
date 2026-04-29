from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl


@dataclass(frozen=True)
class WebhookSignatureResult:
    provider: str
    configured: bool
    header_present: bool
    verified: bool
    mode: str
    expected_header: Optional[str] = None
    error: Optional[str] = None
    warnings: list[str] | None = None

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["warnings"] = value.get("warnings") or []
        return value


def _env(*keys: str) -> Optional[str]:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return None


def _project_prefix(project_slug: str) -> str:
    return project_slug.strip().upper()


def _safe_compare(a: str, b: str) -> bool:
    return hmac.compare_digest((a or "").strip(), (b or "").strip())


def _headers_get(headers: Dict[str, str], key: str) -> Optional[str]:
    target = key.lower()
    for k, v in headers.items():
        if k.lower() == target:
            return v
    return None


def provider_signature_requirements(project_slug: str, provider: str) -> Dict[str, Any]:
    normalized = provider.strip().lower()
    prefix = _project_prefix(project_slug)
    if normalized == "stripe":
        keys = [f"{prefix}_STRIPE_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRET"]
        header = "stripe-signature"
        mode = "stripe_v1_hmac_sha256"
    elif normalized == "twilio":
        keys = [f"{prefix}_TWILIO_AUTH_TOKEN", "TWILIO_AUTH_TOKEN"]
        header = "x-twilio-signature"
        mode = "twilio_hmac_sha1_url_params"
    elif normalized == "canva":
        keys = [f"{prefix}_CANVA_WEBHOOK_SECRET", f"{prefix}_CANVA_CLIENT_SECRET"]
        header = "x-canva-signature"
        mode = "generic_hmac_sha256_raw_body"
    elif normalized == "apliiq":
        keys = [f"{prefix}_APLIIQ_WEBHOOK_SECRET", f"{prefix}_APLIIQ_API_SECRET"]
        header = "x-apliiq-signature"
        mode = "generic_hmac_sha256_raw_body"
    elif normalized == "printful":
        keys = [f"{prefix}_PRINTFUL_WEBHOOK_SECRET"]
        header = "x-pf-signature"
        mode = "generic_hmac_sha256_raw_body"
    else:
        keys = []
        header = None
        mode = "unsupported_provider"
    return {
        "provider": normalized,
        "configured": bool(_env(*keys)) if keys else False,
        "env_keys": keys,
        "expected_header": header,
        "mode": mode,
        "supported": bool(keys),
    }


def signature_readiness_for_project(project_slug: str, providers: list[str]) -> Dict[str, Any]:
    rows = [provider_signature_requirements(project_slug, provider) for provider in sorted(set(providers))]
    supported = [row for row in rows if row.get("supported")]
    unconfigured = [row["provider"] for row in supported if not row.get("configured")]
    return {
        "project_slug": project_slug.strip().lower(),
        "signature_ready": not unconfigured,
        "unconfigured_supported_providers": unconfigured,
        "providers": rows,
    }


def verify_webhook_signature(
    *,
    project_slug: str,
    provider: str,
    headers: Dict[str, str],
    raw_body: bytes,
    payload: Dict[str, Any],
    request_url: str,
) -> WebhookSignatureResult:
    normalized = provider.strip().lower()
    if normalized == "stripe":
        return _verify_stripe(project_slug=project_slug, headers=headers, raw_body=raw_body)
    if normalized == "twilio":
        return _verify_twilio(project_slug=project_slug, headers=headers, raw_body=raw_body, payload=payload, request_url=request_url)
    if normalized == "canva":
        return _verify_generic_hmac(
            project_slug=project_slug,
            provider="canva",
            headers=headers,
            raw_body=raw_body,
            secret_keys=(f"{_project_prefix(project_slug)}_CANVA_WEBHOOK_SECRET", f"{_project_prefix(project_slug)}_CANVA_CLIENT_SECRET"),
            header_names=("x-canva-signature", "canva-signature"),
        )
    if normalized == "apliiq":
        return _verify_generic_hmac(
            project_slug=project_slug,
            provider="apliiq",
            headers=headers,
            raw_body=raw_body,
            secret_keys=(f"{_project_prefix(project_slug)}_APLIIQ_WEBHOOK_SECRET", f"{_project_prefix(project_slug)}_APLIIQ_API_SECRET"),
            header_names=("x-apliiq-signature", "apliiq-signature"),
        )
    if normalized == "printful":
        return _verify_generic_hmac(
            project_slug=project_slug,
            provider="printful",
            headers=headers,
            raw_body=raw_body,
            secret_keys=(f"{_project_prefix(project_slug)}_PRINTFUL_WEBHOOK_SECRET",),
            header_names=("x-pf-signature", "x-printful-signature", "printful-signature"),
        )
    return WebhookSignatureResult(
        provider=normalized,
        configured=False,
        header_present=False,
        verified=False,
        mode="unsupported_provider",
        warnings=["No provider-specific signature verifier is registered."],
    )


def _verify_stripe(*, project_slug: str, headers: Dict[str, str], raw_body: bytes) -> WebhookSignatureResult:
    secret = _env(f"{_project_prefix(project_slug)}_STRIPE_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRET")
    header = _headers_get(headers, "stripe-signature")
    if not secret:
        return WebhookSignatureResult(
            provider="stripe",
            configured=False,
            header_present=bool(header),
            verified=False,
            mode="not_configured",
            expected_header="stripe-signature",
            warnings=["Stripe webhook secret is not configured; live financial webhook trust is not enabled."],
        )
    if not header:
        return WebhookSignatureResult(
            provider="stripe",
            configured=True,
            header_present=False,
            verified=False,
            mode="missing_header",
            expected_header="stripe-signature",
            error="Missing stripe-signature header.",
        )

    pieces: Dict[str, list[str]] = {}
    for item in header.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        pieces.setdefault(key.strip(), []).append(value.strip())
    timestamp = (pieces.get("t") or [None])[0]
    signatures = pieces.get("v1") or []
    if not timestamp or not signatures:
        return WebhookSignatureResult(
            provider="stripe",
            configured=True,
            header_present=True,
            verified=False,
            mode="malformed_header",
            expected_header="stripe-signature",
            error="Stripe signature header is missing timestamp or v1 signature.",
        )

    try:
        ts = int(timestamp)
        if abs(int(time.time()) - ts) > 600:
            return WebhookSignatureResult(
                provider="stripe",
                configured=True,
                header_present=True,
                verified=False,
                mode="timestamp_out_of_tolerance",
                expected_header="stripe-signature",
                error="Stripe signature timestamp is outside the 10-minute tolerance.",
            )
    except Exception:
        return WebhookSignatureResult(
            provider="stripe",
            configured=True,
            header_present=True,
            verified=False,
            mode="invalid_timestamp",
            expected_header="stripe-signature",
            error="Stripe signature timestamp is invalid.",
        )

    signed_payload = timestamp.encode("utf-8") + b"." + raw_body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    verified = any(_safe_compare(expected, sig) for sig in signatures)
    return WebhookSignatureResult(
        provider="stripe",
        configured=True,
        header_present=True,
        verified=verified,
        mode="stripe_v1_hmac_sha256",
        expected_header="stripe-signature",
        error=None if verified else "Stripe signature mismatch.",
    )


def _verify_twilio(*, project_slug: str, headers: Dict[str, str], raw_body: bytes, payload: Dict[str, Any], request_url: str) -> WebhookSignatureResult:
    token = _env(f"{_project_prefix(project_slug)}_TWILIO_AUTH_TOKEN", "TWILIO_AUTH_TOKEN")
    header = _headers_get(headers, "x-twilio-signature")
    if not token:
        return WebhookSignatureResult(
            provider="twilio",
            configured=False,
            header_present=bool(header),
            verified=False,
            mode="not_configured",
            expected_header="x-twilio-signature",
            warnings=["Twilio auth token is not configured; Twilio signature trust is not enabled."],
        )
    if not header:
        return WebhookSignatureResult(
            provider="twilio",
            configured=True,
            header_present=False,
            verified=False,
            mode="missing_header",
            expected_header="x-twilio-signature",
            error="Missing x-twilio-signature header.",
        )

    params: Dict[str, Any] = {}
    content = raw_body.decode("utf-8", errors="ignore")
    if content and "=" in content and "&" in content:
        params = {k: v for k, v in parse_qsl(content, keep_blank_values=True)}
    elif payload:
        params = {str(k): str(v) for k, v in payload.items() if not isinstance(v, (dict, list))}

    signed = request_url
    for key in sorted(params.keys()):
        signed += key + str(params[key])
    digest = hmac.new(token.encode("utf-8"), signed.encode("utf-8"), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    verified = _safe_compare(expected, header)
    return WebhookSignatureResult(
        provider="twilio",
        configured=True,
        header_present=True,
        verified=verified,
        mode="twilio_hmac_sha1_url_params",
        expected_header="x-twilio-signature",
        error=None if verified else "Twilio signature mismatch. Check public URL, proxy host, and submitted params.",
        warnings=[] if params else ["No simple request params were available for Twilio signature base string."],
    )


def _verify_generic_hmac(
    *,
    project_slug: str,
    provider: str,
    headers: Dict[str, str],
    raw_body: bytes,
    secret_keys: tuple[str, ...],
    header_names: tuple[str, ...],
) -> WebhookSignatureResult:
    secret = _env(*secret_keys)
    header_name = None
    header_value = None
    for candidate in header_names:
        value = _headers_get(headers, candidate)
        if value:
            header_name = candidate
            header_value = value
            break
    if not secret:
        return WebhookSignatureResult(
            provider=provider,
            configured=False,
            header_present=bool(header_value),
            verified=False,
            mode="not_configured",
            expected_header=" or ".join(header_names),
            warnings=[f"{provider} webhook secret is not configured; signature trust is not enabled."],
        )
    if not header_value:
        return WebhookSignatureResult(
            provider=provider,
            configured=True,
            header_present=False,
            verified=False,
            mode="missing_header",
            expected_header=" or ".join(header_names),
            error=f"Missing {provider} signature header.",
        )

    digest_hex = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    digest_b64 = base64.b64encode(hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()).decode("utf-8")
    normalized = header_value.strip()
    if normalized.startswith("sha256="):
        normalized = normalized.split("=", 1)[1]
    verified = _safe_compare(digest_hex, normalized) or _safe_compare(digest_b64, normalized)
    return WebhookSignatureResult(
        provider=provider,
        configured=True,
        header_present=True,
        verified=verified,
        mode="generic_hmac_sha256_raw_body",
        expected_header=header_name,
        error=None if verified else f"{provider} signature mismatch.",
    )
