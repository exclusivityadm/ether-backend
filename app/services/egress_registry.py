"""
Ether Egress Registry

Central place to declare routing intent.
No side effects at import time other than registration.
"""

from app.contracts.core import EtherEventType
from app.services.egress_router import egress_router
from app.services.egress_handlers import (
    exclusivity_handler,
    sova_handler,
    audit_handler,
)


def register_egress_routes() -> None:
    """
    Register all known egress routes.
    """

    # ---- Merchant lifecycle ----
    egress_router.register(EtherEventType.MERCHANT_CREATED, audit_handler)
    egress_router.register(EtherEventType.MERCHANT_UPDATED, audit_handler)

    # ---- Customer lifecycle ----
    egress_router.register(EtherEventType.CUSTOMER_UPSERTED, audit_handler)

    # ---- Commerce / loyalty ----
    egress_router.register(EtherEventType.PURCHASE_RECORDED, exclusivity_handler)
    egress_router.register(EtherEventType.LOYALTY_LEDGER_MUTATED, exclusivity_handler)

    # ---- AI ----
    egress_router.register(EtherEventType.AI_INTERACTION, sova_handler)

    # ---- System ----
    egress_router.register(EtherEventType.SYSTEM_AUDIT, audit_handler)
    egress_router.register(EtherEventType.SYSTEM_HEALTH, audit_handler)
