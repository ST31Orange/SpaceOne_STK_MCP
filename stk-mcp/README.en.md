# spaceone-stk-mcp

Python + `win32com` automation for **AGI/Ansys STK 11/12**, exposed three ways:

- **MCP stdio server** for Claude Desktop, Cursor, Claude Code and any MCP client;
- **FastAPI REST kernel** on `127.0.0.1:8080` for the DSH plugin or other programs;
- **Python library / CLI** for scripts, batch jobs and diagnostics.

The TypeScript side never touches COM. Every STK call runs inside one STA COM
apartment thread in the Python process.

## Features

- **77 operations**: scenarios, satellites and orbits (classical, Cartesian, TLE,
  ephemeris file), facilities/places/area targets, sensors, constellations,
  chains, coverage and figures of merit, access and constraints, data providers,
  reports, animation and raw Connect commands.
- **STK 11/12 auto-detection**, preferring STK 11 by default.
- **Verified against real STK 11.2.0**: scenario, orbit, propagation, state,
  access, coverage, report, TLE and save/reopen.
- **Non-destructive lifecycle**: attach to a running STK when possible; do not
  call `Quit` unless `quit=true`. An automation-started instance may exit after
  the last COM reference is released, so save the scenario first.
- **Thread-safe COM**: concurrent REST/MCP calls are serialized onto one
  apartment thread.
- **End-to-end self-test**: 12 steps via CLI or `POST /api/v1/stk/test`.

## Install

Windows, Python ≥ 3.10, a licensed local STK 11 or 12 installation.

```powershell
cd D:\DSH_AI\DSH_spaceone_stk_mcp\spaceone-stk-mcp
python -m pip install -e .
python -m spaceone_spaceone_stk_mcp.cli doctor
```

## Quick start

```powershell
python -m spaceone_spaceone_stk_mcp.cli selftest          # launches STK and runs 12 checks
python -m spaceone_spaceone_stk_mcp.cli serve-http        # REST on 127.0.0.1:8080
python -m spaceone_spaceone_stk_mcp.mcp_server            # MCP stdio
```

MCP client configuration:

```json
{
  "mcpServers": {
    "spaceone-stk-mcp": {
      "command": "python",
      "args": ["-m", "spaceone_spaceone_stk_mcp.mcp_server"],
      "env": { "spaceone_stk_mcp_PROG_ID": "STK11.Application" }
    }
  }
}
```

REST call:

```powershell
$body = @{ arguments = @{ name = "Demo" } } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/api/v1/tools/scenario_create `
  -ContentType application/json -Body $body
```

## CLI

```text
spaceone-stk-mcp serve-mcp | serve-http | list-tools | catalog | call | selftest | doctor
```

## Configuration

Key environment variables (see `.env.example` for all):

| Variable | Default | Meaning |
|---|---|---|
| `spaceone_stk_mcp_PROG_ID` | `auto` | `STK11.Application`, `STK12.Application`, or auto |
| `spaceone_stk_mcp_PREFERRED_VERSION` | `11` | Preferred version in auto mode |
| `spaceone_stk_mcp_VISIBLE` | `true` | Show the GUI for a newly started instance |
| `spaceone_stk_mcp_ATTACH_EXISTING` | `true` | Reuse a running STK instance |
| `spaceone_stk_mcp_AUTO_CONNECT` | `true` | Connect on the first tool call |
| `spaceone_stk_mcp_QUIT_ON_DISCONNECT` | `false` | Quit STK on disconnect |
| `spaceone_stk_mcp_HOST` / `PORT` | `127.0.0.1` / `8080` | REST listener |
| `spaceone_stk_mcp_API_KEY` | empty | Require `X-API-Key` when set |
| `spaceone_stk_mcp_REQUEST_TIMEOUT` | `180` | Per-operation COM budget (seconds) |

## REST API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Lightweight health |
| GET | `/api/v1/tools` | Full catalog with JSON Schemas |
| GET | `/api/v1/tools/{name}` | One operation schema |
| POST | `/api/v1/tools/{name}` | Call with `{"arguments": {...}}` |
| POST | `/api/v1/call` | Generic `{"name", "arguments"}` |
| POST | `/api/v1/session/connect` | Connect |
| DELETE | `/api/v1/session` | Release (optional quit/close) |
| POST | `/api/v1/stk/test` | End-to-end self-test |
| GET | `/docs` | OpenAPI UI |

## Tests

```powershell
python -m pytest -q
$env:spaceone_stk_mcp_RUN_INTEGRATION="1"
python -m pytest -q tests/test_stk_integration.py -s
```

35 unit tests and one real-STK integration test pass on this machine
(STK 11.2.0, ~89 s).

## Layout

```text
src/spaceone_stk_mcp/
├─ config.py, errors.py, timeutil.py, serialization.py
├─ com_worker.py, session.py, enums.py, stk_common.py
├─ tooling.py, registry.py
├─ operations/           # 77 operations by domain
├─ http_server.py        # FastAPI
├─ mcp_server.py         # MCP stdio
├─ selftest.py
└─ cli.py
```

## Limitations

- Windows only.
- TLE / `FromFile` use COM `SetState` first and fall back to STK Connect TCP
  (5001). The Connect port is process-global, so COM is preferred when multiple
  STK versions are running.
- Reports depend on `ReportCreate` and installed report styles.
- Advanced modules (Astrogator targeters, CommSystem, radar, EOIR, SEET) are not
  individually wrapped; use `stk_execute_command` for them.
- Chain strand intervals are limited by the STK COM surface; use reports or
  data providers for detailed strand data.

MIT licensed.
