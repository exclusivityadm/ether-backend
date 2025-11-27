"""
Runtime information helpers for Ether.

These utilities can be used from health checks, diagnostics endpoints,
or logs to understand what version/environment is currently running.
"""

import os
import socket
from typing import Dict


def get_runtime_info() -> Dict[str, str]:
    return {
        "env": os.getenv("ENV", "development"),
        "host": socket.gethostname(),
        "service": os.getenv("ETHER_SERVICE_NAME", "ether-api"),
        "version": os.getenv("ETHER_VERSION", "1.0.0"),
    }
