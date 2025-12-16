"""
Ether Egress Handlers (Skeleton)

These handlers define WHERE events could go.
They are intentionally inert for now.
"""

from app.contracts.core import EventEnvelope


def exclusivity_handler(event: EventEnvelope) -> None:
    """
    Placeholder for Exclusivity downstream routing.
    """
    # Future:
    # - write to Exclusivity queue
    # - emit normalized payload
    pass


def sova_handler(event: EventEnvelope) -> None:
    """
    Placeholder for Sova downstream routing.
    """
    pass


def audit_handler(event: EventEnvelope) -> None:
    """
    Internal audit trail hook.
    """
    pass
