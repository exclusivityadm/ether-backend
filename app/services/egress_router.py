"""
Ether Egress Router

Defines how internal events are routed to downstream systems.
This module is intentionally conservative: routing is explicit,
side effects are minimal, and handlers are opt-in.
"""

from typing import Callable, Dict

from app.contracts.core import EtherEventType, EventEnvelope


# Type alias for downstream handlers
EgressHandler = Callable[[EventEnvelope], None]


class EgressRouter:
    """
    Deterministic routing table for Ether events.
    """

    def __init__(self) -> None:
        self._routes: Dict[EtherEventType, list[EgressHandler]] = {}

    def register(
        self,
        event_type: EtherEventType,
        handler: EgressHandler,
    ) -> None:
        if event_type not in self._routes:
            self._routes[event_type] = []

        self._routes[event_type].append(handler)

    def route(self, event: EventEnvelope) -> bool:
        """
        Route an event to registered handlers.

        Returns True if at least one handler was invoked.
        """
        handlers = self._routes.get(event.event_type, [])
        if not handlers:
            return False

        for handler in handlers:
            handler(event)

        return True


# Singleton router instance
egress_router = EgressRouter()
