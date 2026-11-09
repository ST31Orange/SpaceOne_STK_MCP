"""MCP stdio server exposing the same operation catalog as the REST kernel."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities, ToolsCapability

from .config import Settings
from .errors import StkMcpError
from .registry import get_spec, schemas
from .service import StkService

logger = logging.getLogger(__name__)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def create_server(service: StkService | None = None, settings: Settings | None = None) -> Server:
    settings = settings or Settings.from_env()
    svc = service or StkService(settings)
    server = Server("spaceone-stk-mcp")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=item["name"],
                description=item["description"],
                inputSchema=item["inputSchema"],
            )
            for item in schemas()
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:
            get_spec(name)
        except Exception as exc:
            return [types.TextContent(type="text", text=f"ERROR: {exc}")]
        try:
            result = await asyncio.to_thread(svc.invoke, name, arguments or {})
            return [types.TextContent(type="text", text=_json(result))]
        except StkMcpError as exc:
            return [
                types.TextContent(
                    type="text",
                    text=_json({"ok": False, "error": exc.to_dict()}),
                )
            ]
        except Exception as exc:
            logger.exception("Tool %s failed", name)
            return [types.TextContent(type="text", text=f"ERROR: {exc}")]

    return server


async def run_server(settings: Settings | None = None) -> None:
    settings = settings or Settings.from_env()
    settings.ensure_dirs()
    service = StkService(settings)
    server = create_server(service, settings)
    logger.info("spaceone-stk-mcp stdio server ready (%d tools)", len(schemas()))
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="spaceone-stk-mcp",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(
                        tools=ToolsCapability(listChanged=False)
                    ),
                ),
            )
    finally:
        service.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
