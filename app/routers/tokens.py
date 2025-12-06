import hmac
import base64
import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas.tokens import SignedToken

router = APIRouter(prefix="/tokens", tags=["tokens"])


def _sign(payload: str, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=payload.encode("utf-8"), digestmod=hashlib.sha256)
    return base64.urlsafe_b64encode(mac.digest()).decode("utf-8").rstrip("=")


@router.post("/ephemeral", response_model=SignedToken)
def create_ephemeral_token(minutes: int = 10):
    """Create a short‑lived signed token for frontends / other services.

    This is intentionally simple and self‑contained. It does *not* try to be JWT.
    """
    settings = get_settings()
    secret = settings.APP_NAME  # lightweight stand‑in; you can swap for a real secret later

    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=minutes)
    payload = f"exp={int(expires_at.timestamp())}"
    signature = _sign(payload, secret)
    token = f"{payload}.{signature}"
    return SignedToken(token=token, expires_at=expires_at)


@router.post("/verify")
def verify_token(token: str):
    settings = get_settings()
    secret = settings.APP_NAME

    try:
        payload, signature = token.rsplit(".", 1)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token format")

    expected = _sign(payload, secret)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    parts = dict(p.split("=", 1) for p in payload.split("&") if "=" in p)
    exp_ts = int(parts.get("exp", "0"))
    now_ts = int(datetime.now(tz=timezone.utc).timestamp())
    if now_ts > exp_ts:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    return {"valid": True, "expires_at": datetime.fromtimestamp(exp_ts, tz=timezone.utc)}
