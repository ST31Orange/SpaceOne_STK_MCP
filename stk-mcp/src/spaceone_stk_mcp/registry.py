"""The public operation catalog shared by MCP, HTTP and the DSH plugin."""

from __future__ import annotations

from typing import Any

from . import operations  # noqa: F401  (registration side effects)
from .tooling import TOOLS, ToolSpec, get_spec, invoke, list_specs, validate_arguments

__all__ = [
    "TOOLS",
    "ToolSpec",
    "catalog",
    "get_spec",
    "invoke",
    "list_specs",
    "schemas",
    "tools_by_category",
    "validate_arguments",
]


def schemas() -> list[dict[str, Any]]:
    return [spec.schema() for spec in list_specs()]


def catalog() -> dict[str, Any]:
    categories: dict[str, list[str]] = {}
    for spec in list_specs():
        categories.setdefault(spec.category, []).append(spec.name)
    return {
        "product": "spaceone-stk-mcp",
        "version": "1.0.0",
        "tool_count": len(TOOLS),
        "categories": categories,
        "tools": [spec.catalog_entry() for spec in list_specs()],
    }


def tools_by_category() -> dict[str, list[ToolSpec]]:
    grouped: dict[str, list[ToolSpec]] = {}
    for spec in list_specs():
        grouped.setdefault(spec.category, []).append(spec)
    return grouped
