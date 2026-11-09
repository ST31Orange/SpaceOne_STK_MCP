"""FastAPI REST kernel for the STK toolset (default 127.0.0.1:8080)."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import Settings
from .errors import StkMcpError, StkValidationError
from .registry import catalog
from .service import StkService

logger = logging.getLogger(__name__)


class ToolCallBody(BaseModel):
    arguments: dict[str, Any] = {}


def create_app(service: StkService | None = None, settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    svc = service or StkService(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("STK MCP REST kernel listening on %s:%s", settings.host, settings.port)
        try:
            yield
        finally:
            svc.close()

    app = FastAPI(
        title="STK MCP REST Kernel",
        version="1.0.0",
        description=(
            "HTTP bridge between the DeepSeek Harness TypeScript plugin and AGI STK "
            "11/12. Every operation in /api/v1/tools is the same operation exposed "
            "by the standalone MCP server."
        ),
        lifespan=lifespan,
    )
    app.state.service = svc
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def require_key(x_api_key: str | None = Header(default=None)) -> None:
        if settings.api_key and x_api_key != settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

    @app.exception_handler(StkMcpError)
    async def _stk_error(_request: Request, exc: StkMcpError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={"ok": False, "error": exc.to_dict()},
        )

    @app.exception_handler(Exception)
    async def _unhandled(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled REST error")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "retryable": False,
                },
            },
        )

    @app.get("/")
    def root() -> dict[str, Any]:
        return {
            "name": "spaceone-stk-mcp",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "tools": "/api/v1/tools",
            "selftest": "/api/v1/stk/test",
        }

    @app.get("/health")
    @app.get("/api/v1/health")
    def health() -> dict[str, Any]:
        # Deliberately does not touch the COM apartment: the plugin and process
        # supervisors use this endpoint while a long STK computation may be in
        # flight. Use stk_status for full session/scenario details.
        return {
            "ok": True,
            "service": "spaceone-stk-mcp",
            "connected": svc.session.connected,
            "tool_count": len(catalog()["tools"]),
        }

    @app.get("/api/v1/version")
    def version() -> dict[str, Any]:
        status = svc.status()
        return {
            "ok": True,
            "data": {
                "product": "spaceone-stk-mcp",
                "version": "1.0.0",
                "python_package": "spaceone_stk_mcp",
                "stk_connected": bool(status.get("connected")),
                "stk_version": status.get("version"),
                "prog_id": status.get("prog_id"),
                "tool_count": len(catalog()["tools"]),
                "settings": {
                    "host": settings.host,
                    "port": settings.port,
                    "preferred_version": settings.preferred_version,
                    "auto_connect": settings.auto_connect,
                },
            },
        }

    @app.get("/api/v1/tools", dependencies=[Depends(require_key)])
    def list_tools() -> dict[str, Any]:
        return {"ok": True, "data": catalog()}

    @app.get("/api/v1/tools/{name}", dependencies=[Depends(require_key)])
    def tool_detail(name: str) -> dict[str, Any]:
        for entry in catalog()["tools"]:
            if entry["name"] == name:
                return {"ok": True, "data": entry}
        raise StkValidationError(f"Unknown tool: {name}")

    @app.post("/api/v1/tools/{name}", dependencies=[Depends(require_key)])
    def call_tool(name: str, body: ToolCallBody | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        arguments = body.arguments if body else {}
        try:
            data = svc.invoke(name, arguments)
            return {
                "ok": True,
                "tool": name,
                "data": data,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        except StkMcpError:
            raise
        except Exception as exc:
            raise StkMcpError(str(exc)) from exc

    @app.post("/api/v1/call", dependencies=[Depends(require_key)])
    def call_tool_alias(body: dict[str, Any]) -> dict[str, Any]:
        name = body.get("name") or body.get("tool")
        if not name:
            raise StkValidationError("body must contain 'name'")
        return call_tool(name, ToolCallBody(arguments=body.get("arguments") or {}))

    # Session ----------------------------------------------------------
    @app.post("/api/v1/session/connect", dependencies=[Depends(require_key)])
    def session_connect(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        return {
            "ok": True,
            "data": svc.connect(
                prog_id=payload.get("prog_id"),
                visible=payload.get("visible"),
                user_control=payload.get("user_control"),
                force=bool(payload.get("force", False)),
            ),
        }

    @app.post("/api/v1/session/reconnect", dependencies=[Depends(require_key)])
    def session_reconnect() -> dict[str, Any]:
        return {"ok": True, "data": svc.session.reconnect()}

    @app.delete("/api/v1/session", dependencies=[Depends(require_key)])
    def session_disconnect(
        quit: bool = Query(False), close_scenario: bool = Query(False)
    ) -> dict[str, Any]:
        return {
            "ok": True,
            "data": svc.disconnect(quit=quit, close_scenario=close_scenario),
        }

    # Convenience resource endpoints ----------------------------------
    @app.get("/api/v1/scenario", dependencies=[Depends(require_key)])
    def scenario_get() -> dict[str, Any]:
        return {"ok": True, "data": svc.invoke("scenario_info", {})}

    @app.post("/api/v1/scenario", dependencies=[Depends(require_key)])
    def scenario_create(payload: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "data": svc.invoke("scenario_create", payload)}

    @app.delete("/api/v1/scenario", dependencies=[Depends(require_key)])
    def scenario_close() -> dict[str, Any]:
        return {"ok": True, "data": svc.invoke("scenario_close", {})}

    @app.get("/api/v1/objects", dependencies=[Depends(require_key)])
    def objects_get(class_name: str | None = None) -> dict[str, Any]:
        return {
            "ok": True,
            "data": svc.invoke("object_list", {"class_name": class_name}),
        }

    @app.get("/api/v1/objects/{path:path}", dependencies=[Depends(require_key)])
    def object_get(path: str) -> dict[str, Any]:
        return {"ok": True, "data": svc.invoke("object_info", {"object_name": path})}

    @app.post("/api/v1/access", dependencies=[Depends(require_key)])
    def access(payload: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "data": svc.invoke("access_compute", payload)}

    @app.post("/api/v1/coverage", dependencies=[Depends(require_key)])
    def coverage(payload: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "data": svc.invoke("coverage_compute", payload)}

    # Diagnostics ------------------------------------------------------
    @app.post("/api/v1/stk/test", dependencies=[Depends(require_key)])
    def stk_test(replace_scenario: bool = Query(False)) -> dict[str, Any]:
        started = time.perf_counter()
        report = svc.selftest(replace_scenario=replace_scenario)
        report["elapsed_ms_total"] = round((time.perf_counter() - started) * 1000, 1)
        return {"ok": bool(report.get("passed")), "data": report}

    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = Settings.from_env()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    uvicorn.run(
        "spaceone_stk_mcp.http_server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
