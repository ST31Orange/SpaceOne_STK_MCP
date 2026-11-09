"""Application service shared by the MCP server, REST server and CLI."""

from __future__ import annotations

from typing import Any

from .config import Settings
from .registry import catalog, invoke, schemas
from .selftest import run_selftest
from .session import StkSession


class StkService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.session = StkSession(self.settings)

    # Session -----------------------------------------------------------
    def status(self) -> dict[str, Any]:
        return self.session.status()

    def connect(self, **kwargs: Any) -> dict[str, Any]:
        return self.session.connect(**kwargs)

    def disconnect(self, **kwargs: Any) -> dict[str, Any]:
        return self.session.disconnect(**kwargs)

    # Tools -------------------------------------------------------------
    def schemas(self) -> list[dict[str, Any]]:
        return schemas()

    def catalog(self) -> dict[str, Any]:
        return catalog()

    def invoke(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        return invoke(self.session, name, arguments)

    # Diagnostics -------------------------------------------------------
    def selftest(self, replace_scenario: bool = False) -> dict[str, Any]:
        self.session.ensure_connected()
        return self.session.run(
            lambda: run_selftest(self.session, replace_scenario=replace_scenario),
            timeout=max(self.settings.request_timeout * 2, 300),
        )

    def close(self) -> None:
        self.session.shutdown()
