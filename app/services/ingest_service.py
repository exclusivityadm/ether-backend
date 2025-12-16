from app.contracts.ingress import IngestEventRequest
from app.contracts.egress import IngestEventResponse
from app.contracts.core import EtherSource, EventEnvelope


ALLOWED_SOURCES = {
    EtherSource.EXCLUSIVITY,
    EtherSource.SOVA,
    EtherSource.NIRASOVA_OS,
    EtherSource.ADMIN,
}


def ingest_event(request: IngestEventRequest) -> IngestEventResponse:
    """
    Core ingest logic for Ether.

    This function enforces:
    - internal-only callers
    - strict contract validation (already handled by Pydantic)
    - explicit source allowlist
    """

    event: EventEnvelope = request.event
    meta = event.meta

    # ---- Source enforcement ----
    if meta.source not in ALLOWED_SOURCES:
        raise PermissionError(f"Source '{meta.source}' is not allowed to ingest events")

    # ---- Minimal semantic checks ----
    if not event.event_type:
        raise ValueError("event_type is required")

    if not event.merchant or not event.merchant.merchant_id:
        raise ValueError("merchant.merchant_id is required")

    # ---- Future routing hook (intentionally inert for now) ----
    # This is where:
    # - routing
    # - persistence
    # - fan-out
    # will occur in later steps.

    return IngestEventResponse(
        ok=True,
        request_id=meta.request_id,
        event_id=event.event_id,
        routed=False,
    )
