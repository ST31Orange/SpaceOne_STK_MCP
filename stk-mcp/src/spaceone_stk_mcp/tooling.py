"""Declarative tool registry shared by MCP, REST and the DSH catalog export."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import jsonschema

from .errors import StkMcpError, StkValidationError

Handler = Callable[..., Any]


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Handler
    category: str = "general"
    mutating: bool = False
    returns: str = "object"
    tags: list[str] = field(default_factory=list)

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.parameters,
        }

    def catalog_entry(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "mutating": self.mutating,
            "returns": self.returns,
            "tags": self.tags,
            "parameters": self.parameters,
        }


TOOLS: dict[str, ToolSpec] = {}


def tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    *,
    category: str = "general",
    mutating: bool = False,
    returns: str = "object",
    tags: list[str] | None = None,
) -> Callable[[Handler], Handler]:
    if name in TOOLS:
        raise RuntimeError(f"Duplicate tool registration: {name}")

    def decorator(handler: Handler) -> Handler:
        TOOLS[name] = ToolSpec(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            category=category,
            mutating=mutating,
            returns=returns,
            tags=tags or [],
        )
        return handler

    return decorator


def object_schema(
    properties: dict[str, Any],
    required: list[str] | None = None,
    *,
    description: str | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    if description:
        schema["description"] = description
    return schema


def p(
    type_: str,
    description: str,
    *,
    enum: list[Any] | None = None,
    default: Any = None,
    items: dict[str, Any] | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": type_, "description": description}
    if enum is not None:
        payload["enum"] = enum
    if default is not None:
        payload["default"] = default
    if items is not None:
        payload["items"] = items
    if minimum is not None:
        payload["minimum"] = minimum
    if maximum is not None:
        payload["maximum"] = maximum
    payload.update(extra)
    return payload


def validate_arguments(spec: ToolSpec, arguments: dict[str, Any] | None) -> dict[str, Any]:
    args = dict(arguments or {})
    try:
        jsonschema.validate(args, spec.parameters)
    except jsonschema.ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path) or "(root)"
        raise StkValidationError(
            f"Invalid arguments for {spec.name}: {exc.message}",
            details={"path": path, "validator": exc.validator},
        ) from exc
    return args


def list_specs() -> list[ToolSpec]:
    return list(TOOLS.values())


def get_spec(name: str) -> ToolSpec:
    try:
        return TOOLS[name]
    except KeyError as exc:
        raise StkValidationError(
            f"Unknown tool: {name}",
            details={"available_tools": sorted(TOOLS)},
        ) from exc


def invoke(session: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    """Validate and execute one operation inside the COM apartment."""
    spec = get_spec(name)
    args = validate_arguments(spec, arguments)
    # These three tools must work before a session exists (connect/status), or
    # after it has been released (disconnect).
    if name not in {"stk_connect", "stk_disconnect", "stk_status"}:
        session.ensure_connected()
    try:
        return session.run(lambda: spec.handler(session, **args))
    except StkMcpError:
        raise
    except Exception as exc:  # keep the MCP/HTTP surface structured
        raise StkMcpError(f"{spec.name} failed: {exc}") from exc
