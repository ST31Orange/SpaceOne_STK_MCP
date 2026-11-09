"""Operation modules are imported here for their registration side effects."""

from . import analysis, connection, coverage, equipment, objects, orbit, scenario

__all__ = [
    "analysis",
    "connection",
    "coverage",
    "equipment",
    "objects",
    "orbit",
    "scenario",
]
