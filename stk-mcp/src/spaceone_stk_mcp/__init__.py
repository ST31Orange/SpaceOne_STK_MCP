"""STK MCP — complete STK 11/12 automation as MCP, REST and Python."""

from __future__ import annotations

__version__ = "1.0.0"

from .config import Settings
from .service import StkService

__all__ = ["Settings", "StkService", "__version__"]
