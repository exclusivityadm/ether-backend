# app/schemas/errors.py
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class EtherError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class EtherErrorEnvelope(BaseModel):
    ok: bool = False
    error: EtherError


class EtherErrorResponse:
    @staticmethod
    def _resp(status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
        env = EtherErrorEnvelope(ok=False, error=EtherError(code=code, message=message, details=details))
        return JSONResponse(status_code=status_code, content=env.model_dump())

    @staticmethod
    def unauthorized(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
        return EtherErrorResponse._resp(401, code, message, details)

    @staticmethod
    def forbidden(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
        return EtherErrorResponse._resp(403, code, message, details)

    @staticmethod
    def too_large(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
        return EtherErrorResponse._resp(413, code, message, details)

    @staticmethod
    def rate_limited(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
        return EtherErrorResponse._resp(429, code, message, details)

    @staticmethod
    def bad_request(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
        return EtherErrorResponse._resp(400, code, message, details)
