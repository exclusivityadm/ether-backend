"""
Logging configuration for Ether.

You can import `get_logger` from this module and use it across the codebase
instead of creating ad-hoc loggers everywhere.
"""

import logging
import os
from typing import Optional


LOG_LEVEL = os.getenv("ETHER_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv(
    "ETHER_LOG_FORMAT",
    "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
)


def configure_logging(level: Optional[str] = None) -> None:
    """
    Configure root logging for the Ether application.

    This is safe to call multiple times; it will just update the level/format.
    """
    lvl = (level or LOG_LEVEL).upper()
    logging.basicConfig(level=lvl, format=LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """
    Convenience helper to get a logger configured with Ether defaults.
    """
    configure_logging()
    return logging.getLogger(name)
