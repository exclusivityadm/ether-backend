from fastapi import APIRouter, HTTPException, status
from app.contracts.ingress import IngestEventRequest
from app.contracts.egress import IngestEventResponse
from app.contracts.errors import EtherError, EtherErrorCode
from app.services.ingest_service import ingest_event


router = APIRouter(
    prefix="/ether",
    tags=["ether"],
)


@router.post(
    "/ingest",
    response_model=IngestEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest(request: IngestEventRequest):
    """
    Canonical internal-only ingress endpoint for Ether.

    Accepts ONLY normalized, validated internal events.
    """
    try:
        result = ingest_event(request)
        return result

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
        # Intentionally vague — infra dignity
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=EtherError(
                code=EtherErrorCode.INTERNAL,
                message="Internal Ether error",
                request_id=request.event.meta.request_id,
            ).model_dump(),
        )
