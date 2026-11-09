"""STK session lifecycle and the single COM apartment used by every tool."""

from __future__ import annotations

import gc
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

from .com_worker import ComWorker
from .config import Settings
from .connect_client import ConnectClient
from .errors import (
    StkConnectionError,
    StkMcpError,
    StkNotConnectedError,
    StkOperationError,
    wrap_com_error,
)
from .serialization import describe_com_result, jsonable

logger = logging.getLogger(__name__)
T = TypeVar("T")

_PROG_IDS = {11: "STK11.Application", 12: "STK12.Application", 13: "STK13.Application"}
_PATH_VERSION_RE = re.compile(r"STK[ _-]?(\d+)", re.IGNORECASE)


def _detect_prog_ids(settings: Settings) -> list[str]:
    configured = (settings.stk_prog_id or "auto").strip()
    if configured.lower() != "auto":
        return [configured]
    preferred = settings.preferred_version if settings.preferred_version in _PROG_IDS else 11
    order = [preferred] + [version for version in (11, 12, 13) if version != preferred]
    return [_PROG_IDS[version] for version in order]


class StkSession:
    """Owns the STK application and serializes all COM access."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.settings.ensure_dirs()
        self._worker = ComWorker()
        self._app: Any = None
        self._root: Any = None
        self._connected = False
        self._prog_id: str | None = None
        self._version: str | None = None
        self._pid: int | None = None
        self._attached = False
        self._conversation_state: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------
    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def prog_id(self) -> str | None:
        return self._prog_id

    @property
    def version(self) -> str | None:
        return self._version

    def run(self, fn: Callable[[], T], *, timeout: float | None = None) -> T:
        return self._worker.run(fn, timeout=timeout or self.settings.request_timeout)

    def ensure_connected(self) -> None:
        """Connect on the caller thread when auto-connect is enabled."""
        if self._connected:
            return
        if not self.settings.auto_connect:
            raise StkNotConnectedError("Not connected to STK")
        self.connect()

    def connect(
        self,
        *,
        prog_id: str | None = None,
        visible: bool | None = None,
        user_control: bool | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        if self._connected and not force:
            return self.status()
        if self._connected:
            self.disconnect()

        selected = prog_id or self.settings.stk_prog_id
        candidates = [selected] if selected and selected.lower() != "auto" else _detect_prog_ids(self.settings)
        errors: list[str] = []
        for candidate in candidates:
            try:
                info = self.run(
                    lambda candidate=candidate: self._connect_impl(
                        candidate, visible=visible, user_control=user_control
                    ),
                    timeout=max(self.settings.request_timeout, 60.0),
                )
                logger.info("Connected to %s (%s)", info.get("version"), candidate)
                return info
            except Exception as exc:  # try the next installed STK
                errors.append(f"{candidate}: {exc}")
                logger.warning("Could not connect to %s: %s", candidate, exc)
        raise StkConnectionError(
            "Cannot connect to STK. Tried: " + ", ".join(candidates),
            details=errors,
            hint="Install STK 11 or 12, or set STK_MCP_PROG_ID to the correct "
            "ProgID. Visible STK automation requires a licensed desktop install.",
        )

    def _connect_impl(
        self, prog_id: str, *, visible: bool | None, user_control: bool | None
    ) -> dict[str, Any]:
        if sys.platform != "win32":
            raise StkConnectionError("STK COM automation is only available on Windows")

        # Redirect win32com's generated cache away from C:\Windows\Temp, which
        # is frequently not writable for non-elevated users.
        import win32com

        gen_path = self.settings.data_dir / "gen_py"
        gen_path.mkdir(parents=True, exist_ok=True)
        win32com.__gen_path__ = str(gen_path)

        import pythoncom
        import win32com.client

        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
        app = None
        attached = False
        if self.settings.attach_existing:
            try:
                app = win32com.client.GetActiveObject(prog_id)
                attached = True
            except Exception:
                app = None
        if app is None:
            try:
                if self.settings.attach_existing:
                    app = win32com.client.Dispatch(prog_id)
                else:
                    app = win32com.client.DispatchEx(prog_id)
            except Exception as exc:
                raise wrap_com_error(exc, f"Dispatch({prog_id})") from exc

        try:
            if not attached:
                app.Visible = self.settings.stk_visible if visible is None else visible
                app.UserControl = (
                    self.settings.stk_user_control if user_control is None else user_control
                )
            elif visible is not None or user_control is not None:
                # Only change an existing GUI when the caller explicitly asks.
                if visible is not None:
                    app.Visible = visible
                if user_control is not None:
                    app.UserControl = user_control

            root = app.Personality2
            if root is None:
                raise StkOperationError("STK did not expose the Personality2 interface")
            class_name = str(getattr(root, "ClassName", ""))
            if class_name and class_name != "Application":
                raise StkOperationError(f"Unexpected STK root class: {class_name}")
        except StkMcpError:
            raise
        except Exception as exc:
            raise wrap_com_error(exc, f"Initializing {prog_id}") from exc

        self._app = app
        self._root = root
        self._prog_id = prog_id
        self._attached = attached
        self._connected = True
        self._pid = None
        try:
            self._pid = int(app.ProcessID)
        except Exception:
            pass

        version = self._version_from_prog_id(prog_id)
        try:
            app_path = str(app.Path)
            match = _PATH_VERSION_RE.search(app_path)
            if match:
                version = f"STK {match.group(1)}"
        except Exception:
            pass
        # Exact build number when the Connect server is enabled (STK 11 opens
        # port 5001 by default). The port is process-global, so only accept a
        # reply whose major version matches the instance we actually dispatched.
        major_match = re.search(r"STK(\d+)", prog_id, re.IGNORECASE)
        expected_major = major_match.group(1) if major_match else None
        connect = ConnectClient(self.settings.connect_host, self.settings.connect_port)
        for _ in range(6):
            exact = connect.get_version(timeout=1.0)
            if exact:
                exact_parts = exact.replace("STK", "").strip().split(".")
                if expected_major is None or (exact_parts and exact_parts[0] == expected_major):
                    version = exact
                break
            time.sleep(0.4)
        self._version = version
        scenario = None
        try:
            current = root.CurrentScenario
            if current is not None:
                scenario = {
                    "name": str(current.InstanceName),
                    "start_time": str(current.StartTime),
                    "stop_time": str(current.StopTime),
                }
        except Exception:
            scenario = None
        return {
            "connected": True,
            "prog_id": prog_id,
            "version": version,
            "pid": self._pid,
            "attached": attached,
            "app_path": str(getattr(app, "Path", "")),
            "scenario": scenario,
        }

    @staticmethod
    def _version_from_prog_id(prog_id: str) -> str:
        match = re.search(r"STK(\d+)", prog_id, re.IGNORECASE)
        return f"STK {match.group(1)}" if match else prog_id

    def disconnect(
        self, *, quit: bool | None = None, close_scenario: bool | None = None
    ) -> dict[str, Any]:
        if not self._connected:
            return {"status": "not_connected"}
        do_quit = self.settings.quit_on_disconnect if quit is None else quit
        do_close = (
            self.settings.close_scenario_on_disconnect
            if close_scenario is None
            else close_scenario
        )

        def _impl() -> dict[str, Any]:
            scenario_name = None
            current = None
            try:
                current = self._root.CurrentScenario if self._root is not None else None
                scenario_name = str(current.InstanceName) if current is not None else None
            except Exception:
                scenario_name = None
            # Collect any unreferenced COM proxies while STK is still alive.
            # Collecting after CloseScenario/Quit can raise RPC_E_DISCONNECTED
            # inside a proxy destructor (notably on STK 12).
            current = None
            gc.collect()
            if do_close and scenario_name:
                try:
                    self._root.CloseScenario()
                except Exception:
                    logger.debug("CloseScenario during disconnect failed", exc_info=True)
            if do_quit:
                try:
                    if self._app is not None:
                        self._app.Quit()
                except Exception:
                    logger.debug("Quit during disconnect failed", exc_info=True)
            self._root = None
            self._app = None
            self._connected = False
            self._pid = None
            return {
                "status": "disconnected",
                "quit": do_quit,
                "closed_scenario": bool(do_close and scenario_name),
                "scenario": scenario_name,
            }

        try:
            result = self.run(_impl, timeout=30)
        finally:
            self._connected = False
            self._root = None
            self._app = None
        return result

    def reconnect(self) -> dict[str, Any]:
        prog_id = self._prog_id
        self.disconnect(quit=False, close_scenario=False)
        return self.connect(prog_id=prog_id, force=True)

    def shutdown(self) -> None:
        try:
            if self._connected:
                self.disconnect(quit=False, close_scenario=False)
        finally:
            self._worker.shutdown()

    # ------------------------------------------------------------------
    # COM accessors (only valid inside a ``run`` call)
    # ------------------------------------------------------------------
    @property
    def app(self) -> Any:
        if not self._connected or self._app is None:
            raise StkNotConnectedError("Not connected to STK")
        return self._app

    @property
    def root(self) -> Any:
        if not self._connected or self._root is None:
            raise StkNotConnectedError("Not connected to STK")
        return self._root

    @property
    def scenario(self) -> Any:
        current = self.root.CurrentScenario
        if current is None:
            raise StkOperationError(
                "No scenario is open",
                hint="Call scenario_create or scenario_open first.",
            )
        return current

    def close_scenario(self) -> bool:
        current = self.root.CurrentScenario
        if current is None:
            return False
        self.root.CloseScenario()
        return True

    # ------------------------------------------------------------------
    # Introspection and raw commands
    # ------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        if not self._connected:
            return {
                "connected": False,
                "prog_id": self.settings.stk_prog_id,
                "preferred_version": self.settings.preferred_version,
                "visible": self.settings.stk_visible,
                "user_control": self.settings.stk_user_control,
                "attach_existing": self.settings.attach_existing,
                "scenario": None,
            }

        def _impl() -> dict[str, Any]:
            current = None
            try:
                scenario = self._root.CurrentScenario
                if scenario is not None:
                    current = {
                        "name": str(scenario.InstanceName),
                        "start_time": str(scenario.StartTime),
                        "stop_time": str(scenario.StopTime),
                    }
            except Exception:
                current = None
            app_path = None
            visible = None
            user_control = None
            try:
                app_path = str(self._app.Path)
            except Exception:
                pass
            try:
                visible = bool(self._app.Visible)
                user_control = bool(self._app.UserControl)
            except Exception:
                pass
            return {
                "connected": True,
                "prog_id": self._prog_id,
                "version": self._version,
                "pid": self._pid,
                "attached": self._attached,
                "app_path": app_path,
                "visible": visible,
                "user_control": user_control,
                "scenario": current,
            }

        try:
            return self.run(_impl, timeout=20)
        except Exception as exc:
            return {"connected": False, "error": str(exc), "prog_id": self._prog_id}

    def configure_gui(
        self, *, visible: bool | None = None, user_control: bool | None = None
    ) -> dict[str, Any]:
        """Switch headed/headless or user control without losing the scenario."""
        if not self._connected:
            return self.status()

        def _impl() -> dict[str, Any]:
            if visible is not None:
                self._app.Visible = bool(visible)
            if user_control is not None:
                self._app.UserControl = bool(user_control)
            return self.status()

        try:
            return self.run(_impl, timeout=20)
        except Exception as exc:
            raise wrap_com_error(exc, "Configuring STK window mode") from exc

    def execute_command(self, command: str, transport: str = "com") -> dict[str, Any]:
        transport = (transport or "com").lower()
        if transport not in {"com", "tcp", "auto"}:
            raise StkOperationError(
                f"Unknown transport {transport!r}; use com, tcp or auto"
            )

        def _com() -> dict[str, Any]:
            result = self.root.ExecuteCommand(command)
            payload = describe_com_result(result)
            payload["transport"] = "com"
            payload["command"] = command
            return payload

        def _tcp() -> dict[str, Any]:
            client = ConnectClient(self.settings.connect_host, self.settings.connect_port)
            if not client.is_available():
                raise StkOperationError(
                    "STK Connect server is not listening",
                    details={"host": self.settings.connect_host, "port": self.settings.connect_port},
                    hint="Enable Connect in STK: Edit > Preferences > Connect, or use transport=com.",
                )
            return client.execute(command, timeout=60).to_dict()

        if transport == "tcp":
            return self.run(_tcp, timeout=90)
        if transport == "auto":
            try:
                return self.run(_com, timeout=90)
            except StkMcpError:
                return self.run(_tcp, timeout=90)
        try:
            return self.run(_com, timeout=90)
        except StkMcpError:
            raise
        except Exception as exc:
            raise wrap_com_error(exc, f"ExecuteCommand({command[:80]})") from exc

    def get_screenshot(self) -> dict[str, Any]:
        """Return basic window metadata; image capture is intentionally not faked."""
        return self.status()

    # ------------------------------------------------------------------
    # Small helpers used by selftest and diagnostics
    # ------------------------------------------------------------------
    def file_info(self, path: str | Path) -> dict[str, Any]:
        p = Path(path)
        return {"path": str(p.resolve()), "exists": p.exists(), "size": p.stat().st_size if p.exists() else 0}

    def to_json(self, value: Any) -> Any:
        return jsonable(value)
