"""Command-line entry point for the STK MCP product."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from . import __version__
from .config import Settings
from .registry import catalog, schemas
from .service import StkService


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _cmd_serve_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import run_server
    import asyncio

    settings = Settings.from_env()
    _configure_logging(args.log_level or settings.log_level)
    asyncio.run(run_server(settings))
    return 0


def _cmd_serve_http(args: argparse.Namespace) -> int:
    import uvicorn

    settings = Settings.from_env()
    if args.host:
        settings.host = args.host
    if args.port:
        settings.port = args.port
    _configure_logging(args.log_level or settings.log_level)
    uvicorn.run(
        "spaceone_stk_mcp.http_server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
    return 0


def _cmd_list_tools(args: argparse.Namespace) -> int:
    tools = schemas()
    if args.json:
        _print_json(tools)
        return 0
    for item in tools:
        print(f"{item['name']:<32} {item['description']}")
    print(f"\n{len(tools)} tools")
    return 0


def _cmd_catalog(args: argparse.Namespace) -> int:
    _print_json(catalog())
    return 0


def _cmd_call(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    service = StkService(settings)
    arguments = {}
    if args.args:
        try:
            arguments = json.loads(args.args)
        except json.JSONDecodeError as exc:
            print(f"Invalid --args JSON: {exc}", file=sys.stderr)
            return 2
    try:
        result = service.invoke(args.tool, arguments)
        _print_json({"ok": True, "tool": args.tool, "data": result})
        return 0
    except Exception as exc:
        _print_json({"ok": False, "tool": args.tool, "error": str(exc)})
        return 1
    finally:
        service.close()


def _cmd_selftest(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    _configure_logging(args.log_level or settings.log_level)
    service = StkService(settings)
    try:
        report = service.selftest(replace_scenario=args.replace_scenario)
        _print_json(report)
        return 0 if report.get("passed") else 1
    finally:
        service.close()


def _cmd_doctor(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    checks: list[dict[str, Any]] = []

    def check(name: str, fn: Any) -> None:
        try:
            value = fn()
            checks.append({"check": name, "ok": True, "value": value})
        except Exception as exc:
            checks.append({"check": name, "ok": False, "error": str(exc)})

    check("python", lambda: sys.version.split()[0])
    check("platform", lambda: sys.platform)

    def _win32com() -> str:
        import win32com  # noqa: F401
        import pythoncom  # noqa: F401

        return "pywin32 available"

    check("pywin32", _win32com)

    def _progids() -> dict[str, bool]:
        import winreg

        result = {}
        for progid in ("STK11.Application", "STK12.Application"):
            try:
                winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid + r"\CLSID").Close()
                result[progid] = True
            except Exception:
                result[progid] = False
        return result

    check("stk_progids", _progids)

    def _connect_port() -> bool:
        from .connect_client import ConnectClient

        return ConnectClient(settings.connect_host, settings.connect_port).is_available()

    check("stk_connect_port", _connect_port)
    _print_json({"ok": all(item["ok"] for item in checks), "checks": checks})
    return 0 if all(item["ok"] for item in checks) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spaceone-stk-mcp",
        description="STK 11/12 toolset: MCP stdio server, REST kernel and CLI.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    serve_mcp = sub.add_parser("serve-mcp", help="Run the MCP stdio server (default)")
    serve_mcp.add_argument("--log-level", default=None)
    serve_mcp.set_defaults(func=_cmd_serve_mcp)

    serve_http = sub.add_parser("serve-http", help="Run the FastAPI REST kernel")
    serve_http.add_argument("--host", default=None)
    serve_http.add_argument("--port", type=int, default=None)
    serve_http.add_argument("--log-level", default=None)
    serve_http.set_defaults(func=_cmd_serve_http)

    list_tools = sub.add_parser("list-tools", help="List registered tools")
    list_tools.add_argument("--json", action="store_true")
    list_tools.set_defaults(func=_cmd_list_tools)

    catalog_cmd = sub.add_parser("catalog", help="Print the machine-readable catalog")
    catalog_cmd.set_defaults(func=_cmd_catalog)

    call = sub.add_parser("call", help="Call one tool from the command line")
    call.add_argument("tool")
    call.add_argument("--args", default="{}", help="JSON object of arguments")
    call.set_defaults(func=_cmd_call)

    selftest = sub.add_parser("selftest", help="Run the STK end-to-end smoke test")
    selftest.add_argument("--replace-scenario", action="store_true")
    selftest.add_argument("--log-level", default=None)
    selftest.set_defaults(func=_cmd_selftest)

    doctor = sub.add_parser("doctor", help="Check Python, pywin32, STK ProgIDs and Connect")
    doctor.set_defaults(func=_cmd_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        return _cmd_serve_mcp(args)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
