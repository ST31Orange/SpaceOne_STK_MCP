"""Runtime configuration for the STK MCP kernel.

All values can be supplied through environment variables. ``.env`` files are
loaded when ``python-dotenv`` is available, but the package never requires it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # optional, keeps the package usable in a bare venv
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is a convenience only
    pass


def _env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip() != "":
            return value.strip()
    return default


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _float(value: str | None, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    """Connection, server and scenario defaults."""

    # STK application selection. "auto" tries the preferred version first and
    # then the other installed version.
    stk_prog_id: str = "auto"
    preferred_version: int = 11
    stk_visible: bool = True
    stk_user_control: bool = True
    attach_existing: bool = True
    auto_connect: bool = True
    quit_on_disconnect: bool = False
    close_scenario_on_disconnect: bool = False

    # Scenario defaults.
    default_scenario_name: str = "STK_MCP_Scenario"
    default_duration_hours: float = 24.0
    default_step_sec: float = 60.0
    data_dir: Path = field(default_factory=lambda: Path.home() / ".spaceone-stk-mcp")

    # HTTP server.
    host: str = "127.0.0.1"
    port: int = 8080
    api_key: str | None = None
    request_timeout: float = 180.0
    max_rows: int = 20000
    # Refuse to save/report a scenario folder larger than this (bytes).
    max_save_bytes: int = 2_000_000_000

    # Optional Connect server used for the raw-command escape hatch.
    connect_host: str = "127.0.0.1"
    connect_port: int = 5001

    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = _env("STK_MCP_DATA_DIR", default=None)
        return cls(
            stk_prog_id=_env("STK_MCP_PROG_ID", "STK_PROG_ID", default="auto") or "auto",
            preferred_version=_int(
                _env("STK_MCP_PREFERRED_VERSION", "STK_PREFERRED_VERSION"), 11
            ),
            stk_visible=_bool(_env("STK_MCP_VISIBLE", "STK_VISIBLE"), True),
            stk_user_control=_bool(
                _env("STK_MCP_USER_CONTROL", "STK_USER_CONTROL"), True
            ),
            attach_existing=_bool(_env("STK_MCP_ATTACH_EXISTING"), True),
            auto_connect=_bool(_env("STK_MCP_AUTO_CONNECT"), True),
            quit_on_disconnect=_bool(_env("STK_MCP_QUIT_ON_DISCONNECT"), False),
            close_scenario_on_disconnect=_bool(
                _env("STK_MCP_CLOSE_SCENARIO_ON_DISCONNECT"), False
            ),
            default_scenario_name=_env(
                "STK_MCP_DEFAULT_SCENARIO", default="STK_MCP_Scenario"
            )
            or "STK_MCP_Scenario",
            default_duration_hours=_float(
                _env("STK_MCP_DEFAULT_DURATION_HOURS"), 24.0
            ),
            default_step_sec=_float(_env("STK_MCP_DEFAULT_STEP"), 60.0),
            data_dir=Path(data_dir).expanduser() if data_dir else Path.home() / ".spaceone-stk-mcp",
            host=_env("STK_MCP_HOST", default="127.0.0.1") or "127.0.0.1",
            port=_int(_env("STK_MCP_PORT"), 8080),
            api_key=_env("STK_MCP_API_KEY", default=None),
            request_timeout=_float(_env("STK_MCP_REQUEST_TIMEOUT"), 180.0),
            max_rows=_int(_env("STK_MCP_MAX_ROWS"), 20000),
            max_save_bytes=_int(_env("STK_MCP_MAX_SAVE_BYTES"), 2_000_000_000),
            connect_host=_env("STK_MCP_CONNECT_HOST", default="127.0.0.1")
            or "127.0.0.1",
            connect_port=_int(_env("STK_MCP_CONNECT_PORT"), 5001),
            log_level=(_env("STK_MCP_LOG_LEVEL", default="INFO") or "INFO").upper(),
        )

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
