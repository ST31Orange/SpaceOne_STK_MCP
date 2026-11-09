"""Connection, capabilities, raw command and self-test operations."""

from __future__ import annotations

from typing import Any

from ..enums import OBJECT_TYPE
from ..selftest import run_selftest
from ..tooling import object_schema, p, tool

_SESSION_ID = p("string", "Optional scenario name to report",)


@tool(
    "stk_connect",
    "Launch or attach to STK 11/12 through COM. Existing instances are reused; "
    "a new instance is started only when no STK automation object is running.",
    object_schema(
        {
            "prog_id": p(
                "string",
                "STK ProgID. Omit to use auto-detection (STK 11 preferred, then STK 12).",
                enum=["STK11.Application", "STK12.Application"],
            ),
            "visible": p("boolean", "Show the STK desktop window (headed mode)", default=True),
            "user_control": p("boolean", "Allow the user to interact with STK", default=True),
            "force": p("boolean", "Reconnect even if a session is already active", default=False),
        }
    ),
    category="connection",
    mutating=True,
    returns="session status",
    tags=["connection", "stk"],
)
def stk_connect(
    session: Any,
    prog_id: str | None = None,
    visible: bool | None = None,
    user_control: bool | None = None,
    force: bool = False,
) -> dict[str, Any]:
    if session.connected and not force:
        # Switch headed/headless (or user-control) without tearing down the
        # scenario. This is the per-call mode switch.
        if visible is not None or user_control is not None:
            session.configure_gui(visible=visible, user_control=user_control)
        return session.status()
    return session.connect(
        prog_id=prog_id, visible=visible, user_control=user_control, force=force
    )


@tool(
    "stk_disconnect",
    "Release the STK COM reference. Do NOT call this at the end of a modeling or "
    "analysis task: leave the scenario open for the user. The STK process is not "
    "quit and the scenario is not closed by default.",
    object_schema(
        {
            "quit": p("boolean", "Quit the STK application", default=False),
            "close_scenario": p("boolean", "Close the current scenario first", default=False),
        }
    ),
    category="connection",
    mutating=True,
    returns="disconnect status",
)
def stk_disconnect(
    session: Any, quit: bool = False, close_scenario: bool = False
) -> dict[str, Any]:
    return session.disconnect(quit=quit, close_scenario=close_scenario)


@tool(
    "stk_status",
    "Report whether the kernel is connected, the STK version/PID and the open scenario.",
    object_schema({}),
    category="connection",
    returns="session status",
)
def stk_status(session: Any) -> dict[str, Any]:
    return session.status()


@tool(
    "stk_capabilities",
    "List the STK version, object types supported by the installed license, and "
    "the available Connect port. Useful before building a workflow.",
    object_schema({}),
    category="connection",
    returns="capability map",
)
def stk_capabilities(session: Any) -> dict[str, Any]:
    root = session.root
    features: list[str] = []
    unsupported: list[str] = []
    try:
        available = root.AvailableFeatures
        for name, code in OBJECT_TYPE.items():
            try:
                if bool(available.IsObjectTypeAvailable(code)):
                    features.append(name)
                else:
                    unsupported.append(name)
            except Exception:
                continue
    except Exception:
        pass
    scenario = None
    try:
        current = root.CurrentScenario
        if current is not None:
            scenario = str(current.InstanceName)
    except Exception:
        pass
    return {
        "version": session.version,
        "prog_id": session.prog_id,
        "pid": session._pid,
        "scenario": scenario,
        "object_types_available": features,
        "object_types_unavailable": unsupported,
        "connect_port": session.settings.connect_port,
        "connect_enabled": _connect_port_open(session),
        "transport": "COM (win32com) with optional Connect TCP escape hatch",
    }


def _connect_port_open(session: Any) -> bool:
    from ..connect_client import ConnectClient

    return ConnectClient(session.settings.connect_host, session.settings.connect_port).is_available()


@tool(
    "stk_execute_command",
    "Execute a raw STK Connect command. transport=com uses the COM ExecuteCommand "
    "path; transport=tcp uses the Connect socket and returns raw reply data.",
    object_schema(
        {
            "command": p("string", "Connect command, e.g. 'GetSTKVersion /'"),
            "transport": p(
                "string",
                "Execution channel",
                enum=["com", "tcp", "auto"],
                default="com",
            ),
        },
        ["command"],
    ),
    category="connection",
    mutating=True,
    returns="command result",
    tags=["connect", "escape-hatch"],
)
def stk_execute_command(
    session: Any, command: str, transport: str = "com"
) -> dict[str, Any]:
    if not command.strip():
        from ..errors import StkValidationError

        raise StkValidationError("command must not be empty")
    return session.execute_command(command, transport=transport)


@tool(
    "stk_selftest",
    "Run an end-to-end STK smoke test: scenario, satellite orbit, propagation, "
    "state query, facility, access, coverage and report. With an existing "
    "scenario open it performs read-only checks unless replace_scenario=true.",
    object_schema(
        {
            "replace_scenario": p(
                "boolean",
                "Close the current scenario and run the full write test",
                default=False,
            )
        }
    ),
    category="connection",
    mutating=True,
    returns="step-by-step self-test report",
    tags=["diagnostics", "selftest"],
)
def stk_selftest(session: Any, replace_scenario: bool = False) -> dict[str, Any]:
    return run_selftest(session, replace_scenario=replace_scenario)
