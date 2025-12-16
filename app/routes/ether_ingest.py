# app/routes/ether_ingest.py

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional

from app.contracts.ingress import IngestEventRequest
from app.contracts.egress import IngestEventResponse
from app.contracts.errors import EtherError, EtherErrorCode
from app.contracts.core import EtherSource
from app.services.ingest_service import ingest_event


router = APIRouter(
    prefix="/ether",
    tags=["ether-internal"],
)


# -------------------------------
# INTERNAL SECURITY DEPENDENCY
# -------------------------------

def require_internal_service(
    x_ether_service: Optional[str] = Header(None),
):
    """
    Enforces internal-only access to Ether.

    All callers MUST send:
      X-Ether-Service: <service-name>

    This is intentionally simple and strict.
    """
    if not x_ether_service:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=EtherError(
                code=EtherErrorCode.UNAUTHORIZED_CALLER,
                message="Missing X-Ether-Service header",
            ).model_dump(),
        )

    try:
        EtherSource(x_ether_service)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=EtherError(
                code=EtherErrorCode.FORBIDDEN,
                message=f"Service '{x_ether_service}' is not authorized to call Ether",
            ).model_dump(),
        )

    return x_ether_service


# -------------------------------
# CANONICAL INGEST ENDPOINT
# -------------------------------

@router.post(
    "/ingest",
    response_model=IngestEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_internal_service)],
)
async def ingest(request: IngestEventRequest):
    """
    Canonical internal-only ingress endpoint for Ether.

    This endpoint is NOT public.
    It is NOT merchant-facing.
    It is NOT webhook-facing.
    """
    try:
        return ingest_event(request)

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=EtherError(
                code=EtherErrorCode.FORBIDDEN,
                message=str(e),
                request_id=request.event.meta.request_id,
            ).model_dump(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=EtherError(
                code=EtherErrorCode.INVALID_REQUEST,
                message=str(e),
                request_id=request.event.meta.request_id,
            ).model_dump(),
        )

    except Exception:
        # Intentionally vague — no internal leakage
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=EtherError(
                code=EtherErrorCode.INTERNAL,
                message="Internal Ether error",
                request_id=request.event.meta.request_id,
            ).model_dump(),
        )
