"""
Core system utilities for Ether.

This package is the home for:
- keep_alive: background uptime/heartbeat helpers
- future: logging, settings helpers, task runners, etc.

Nothing in here should import from high-level app modules
(routers, API handlers, etc.) to avoid circular dependencies.
"""
