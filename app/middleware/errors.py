# app/middleware/errors.py
from __future__ import annotations

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.errors import EtherErrorEnvelope

log = logging.getLogger("ether_v2.errors")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Always normalize, never leak stack traces.
        env = EtherErrorEnvelope(
            ok=False,
            error={
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail if isinstance(exc.detail, str) else "Request failed.",
                "details": None,
            },
        )
        return JSONResponse(status_code=exc.status_code, content=env.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log.exception("Unhandled exception: %s", exc)
        env = EtherErrorEnvelope(
            ok=False,
            error={
                "code": "ETHER_INTERNAL_ERROR",
                "message": "Internal error.",
                "details": None,
            },
        )
        return JSONResponse(status_code=500, content=env.model_dump())
