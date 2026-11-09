"""Structured errors shared by the library, MCP server and REST layer."""

from __future__ import annotations

from typing import Any


class StkMcpError(Exception):
    """Base error with a stable machine-readable code."""

    code = "STK_MCP_ERROR"
    http_status = 500
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: Any = None,
        hint: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details
        self.hint = hint
        if retryable is not None:
            self.retryable = retryable

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details is not None:
            payload["details"] = self.details
        if self.hint:
            payload["hint"] = self.hint
        return payload


class StkConnectionError(StkMcpError):
    code = "STK_CONNECTION_ERROR"
    http_status = 503
    retryable = True


class StkNotConnectedError(StkConnectionError):
    code = "STK_NOT_CONNECTED"


class StkOperationError(StkMcpError):
    code = "STK_OPERATION_ERROR"
    http_status = 422


class StkValidationError(StkMcpError):
    code = "INVALID_ARGS"
    http_status = 400


class StkNotFoundError(StkOperationError):
    code = "OBJECT_NOT_FOUND"
    http_status = 404


class StkCapabilityError(StkOperationError):
    code = "CAPABILITY_UNAVAILABLE"
    http_status = 501


class StkTimeoutError(StkMcpError):
    code = "STK_TIMEOUT"
    http_status = 504
    retryable = True


class ComOperationError(StkOperationError):
    code = "STK_COM_ERROR"


def wrap_com_error(exc: BaseException, context: str = "") -> ComOperationError:
    """Translate a pywin32 COM error into a readable structured error."""
    hresult = None
    message = str(exc)
    details: Any = None
    args = getattr(exc, "args", None)
    if args and isinstance(args, tuple):
        # pywintypes.com_error: (hresult, text, excepinfo, argerr)
        if len(args) >= 2 and isinstance(args[0], int):
            hresult = args[0]
        if len(args) >= 3 and isinstance(args[2], tuple) and len(args[2]) >= 3:
            description = args[2][2]
            if description:
                message = str(description)
            details = {
                "source": args[2][1] if len(args[2]) > 1 else None,
                "description": args[2][2] if len(args[2]) > 2 else None,
                "help_file": args[2][3] if len(args[2]) > 3 else None,
            }
    prefix = f"{context}: " if context else ""
    return ComOperationError(
        f"{prefix}{message}",
        details={"hresult": hresult, **(details or {})},
        hint="Check that the object exists in the current scenario and that the "
        "operation is supported by the installed STK version.",
    )
