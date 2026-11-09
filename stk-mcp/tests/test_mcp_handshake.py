from __future__ import annotations

import os
import sys

import pytest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_mcp_handshake_and_status_tool():
    env = dict(os.environ)
    env["STK_MCP_AUTO_CONNECT"] = "false"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "spaceone_stk_mcp.mcp_server"],
        env=env,
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init = await session.initialize()
            assert init.serverInfo.name == "spaceone-stk-mcp"
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            assert len(names) >= 50
            assert "stk_status" in names
            assert "satellite_set_orbit" in names
            result = await session.call_tool("stk_status", {})
            assert result.content
            text = result.content[0].text
            assert '"connected": false' in text
