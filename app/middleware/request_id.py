"""
Simple request ID middleware.

This can help correlate logs to individual HTTP requests.

Usage (in app.main):

    from app.middleware.request_id import RequestIDMiddleware
    app.add_middleware(RequestIDMiddleware)

"""

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        # Inject into state for handlers to use if desired
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
