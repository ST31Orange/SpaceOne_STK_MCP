# spaceone-stk-plugin

A native DeepSeek Harness plugin for AGI/Ansys STK 11/12. The TypeScript shell
registers `stk_*` Function Calling tools and forwards every call over HTTP to the
Python kernel; all STK COM work happens in Python. There is no `winax` and no
COM call from TypeScript.

- **42 tools**: 40 curated operations + `stk_call` (all 77 operations) +
  `stk_list_tools`.
- Default kernel: `http://127.0.0.1:8080`.
- With `autoStart=true`, the first tool call starts
  `python -m spaceone_spaceone_stk_mcp.cli serve-http` when the kernel is not running.
- Verified in DSH headless: `module → apply → registered:42`.

## Prerequisites

1. Windows and a licensed STK 11 or 12 installation.
2. Python 3.10+ with the kernel installed:

   ```powershell
   cd D:\DSH_AI\DSH_spaceone_stk_mcp\spaceone-stk-mcp
   python -m pip install -e .
   python -m spaceone_spaceone_stk_mcp.cli doctor
   ```

3. A DSH profile (usually `desktop` or `web`).

## Install

```powershell
dsh plugin --profile desktop add "link:D:\DSH_AI\DSH_spaceone_stk_mcp\spaceone-stk-plugin"
```

Restart DSH or open a new session. Remove with:

```powershell
dsh plugin --profile desktop remove spaceone-stk-plugin
```

To test without touching your main profile:

```powershell
dsh plugin --profile stktest add "link:D:\DSH_AI\DSH_spaceone_stk_mcp\spaceone-stk-plugin"
# delete ~/.dsh/profiles/stktest when done
```

## Tools

| DSH tool | Python operation | Purpose |
|---|---|---|
| `stk_connect` | `stk_connect` | Attach/launch STK |
| `stk_status` | `stk_status` | Connection and scenario status |
| `stk_scenario_create` | `scenario_create` | Create a scenario |
| `stk_scenario_info` | `scenario_info` | Scenario and object summary |
| `stk_scenario_set_time` | `scenario_set_time` | Change time bounds |
| `stk_satellite_create` | `satellite_create` | Create a satellite |
| `stk_satellite_set_orbit` | `satellite_set_orbit` | Classical / Cartesian / TLE / file |
| `stk_satellite_state` | `satellite_state` | Position, velocity, LLA, elements |
| `stk_satellite_ephemeris` | `satellite_ephemeris` | Sampled ephemeris / CSV |
| `stk_facility_create` | `facility_create` | Ground facility |
| `stk_sensor_create` | `sensor_create` | Simple-cone sensor |
| `stk_access_compute` | `access_compute` | Access intervals |
| `stk_coverage_create` | `coverage_create` | Coverage definition |
| `stk_coverage_set_grid` | `coverage_set_grid` | Global / lat-lon grid |
| `stk_coverage_add_asset` | `coverage_add_asset` | Add asset |
| `stk_coverage_remove_asset` | `coverage_remove_asset` | Remove asset |
| `stk_coverage_compute` | `coverage_compute` | Compute + statistics |
| `stk_coverage_stats` | `coverage_stats` | Coverage statistics/time series |
| `stk_coverage_fom_create` | `coverage_fom_create` | Create coverage FOM |
| `stk_coverage_fom_query` | `coverage_fom_query` | Query FOM |
| `stk_coverage_grid_inspector` | `coverage_grid_inspector` | Point coverage inspector |
| `stk_data_provider_list` | `data_provider_list` | List data providers |
| `stk_data_provider_query` | `data_provider_query` | Arbitrary data provider |
| `stk_report_create` | `report_create` | STK report export |
| `stk_object_list` | `object_list` | Object inventory |
| `stk_equipment_create` | `equipment_create` | Antenna / receiver / transmitter / radar |
| `stk_equipment_configure` | `equipment_configure` | Configure equipment model |
| `stk_equipment_list` | `equipment_list` | List equipment on a parent |
| `stk_platform_create` | `platform_create` | Create aircraft / ship / ground vehicle |
| `stk_platform_set_waypoints` | `platform_set_waypoints` | Aircraft / ship / ground-vehicle route |
| `stk_area_target_create` | `area_target_create` | Create an area target |
| `stk_area_target_set_polygon` | `area_target_set_polygon` | Polygon area target |
| `stk_chain_create` | `chain_create` | Create a chain |
| `stk_chain_compute_access` | `chain_compute_access` | Chain access intervals |
| `stk_constellation_build_walker` | `constellation_build_walker` | Walker Delta/Star batch build |
| `stk_astrogator_summary` | `astrogator_summary` | Astrogator segment list |
| `stk_astrogator_run` | `astrogator_run` | Run Astrogator MCS |
| `stk_report_list_styles` | `report_list_styles` | List report styles |
| `stk_execute_command` | `stk_execute_command` | Raw Connect command |
| `stk_selftest` | `stk_selftest` | End-to-end STK self-test |
| `stk_call` | any | Call any of the 77 operations |
| `stk_list_tools` | local | 77-operation catalog; `include_schema=true` adds schemas |

## Configuration

DSH composes profiles from `cordis.patch.yml`, not `config.toml`. The bundle
ships this default row:

```yaml
- insert:
    - id: spaceone-stk-plugin
      name: spaceone-stk-plugin
      config:
        baseUrl: http://127.0.0.1:8080
        autoStart: true
        pythonPath: python
        timeoutMs: 180000
```

Override it in the profile's own `cordis.patch.yml`:

```yaml
- id: spaceone-stk-plugin
  config:
    baseUrl: http://127.0.0.1:8080
    autoStart: true
    pythonPath: C:\Python312\python.exe
    timeoutMs: 300000
    serverPort: 8080
```

`config` is replaced wholesale, so restate every field you need.

An equivalent TOML reference is in [`config.example.toml`](config.example.toml).

| Field | Default | Meaning |
|---|---|---|
| `baseUrl` | `http://127.0.0.1:8080` | Python kernel URL |
| `apiKey` | empty | Sent as `X-API-Key` when the kernel requires it |
| `timeoutMs` | `180000` | Per-call budget |
| `autoStart` | `true` | Start the Python kernel on first use |
| `pythonPath` | `python` | Python with `spaceone-stk-mcp` installed |
| `serverHost` | `127.0.0.1` | Auto-start host |
| `serverPort` | `8080` | Auto-start port |
| `startupTimeoutMs` | `30000` | Health-check wait |

## Manual kernel

```powershell
python -m spaceone_spaceone_stk_mcp.cli serve-http --host 127.0.0.1 --port 8080
curl.exe http://127.0.0.1:8080/health
```

`connected:false` at health time is expected; STK connects lazily on the first
tool call so plugin activation is not blocked by a 30–60 s STK launch.

## Architecture

```text
DSH Agent
   │ stk_scenario_create
   ▼
spaceone-stk-plugin (TypeScript)
   │ ctx.tools.register(defineTool({...}))
   │ POST /api/v1/tools/scenario_create
   ▼
spaceone-stk-mcp FastAPI (Python)
   │ registry → StkSession → single STA COM thread
   ▼
pywin32 → STK 11/12 COM
```

The plugin uses DSH's `defineTool` when `@deepseek-ai/dsh-tools` resolves. In
third-party profiles it usually does not, so the plugin falls back to a local
`defineTool` of the same shape that registers standard JSON Schema directly.
DSH has been verified to accept and register all 42 definitions this way.

Schemas are generated from the Python catalog by
`spaceone-stk-mcp/scripts/export_catalog.py`, so the two products cannot drift.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `STK_KERNEL_UNREACHABLE` | Start the Python server or check `baseUrl` |
| `STK_KERNEL_START_TIMEOUT` | Wrong `pythonPath` or `spaceone-stk-mcp` not installed |
| `STK_NOT_CONNECTED` | Call `stk_connect`; check STK licensing |
| No `stk_*` tools | Reinstall in the active profile and restart DSH |
| 401 | `apiKey` does not match `spaceone_stk_mcp_API_KEY` |
| Port conflict | Change `baseUrl` and `serverPort` |

## Verification

- `npm test`: 7 passed (mock HTTP, schema conversion, error mapping, autoStart).
- DSH headless activation marker: `module → apply → registered:42:fallback →
  selftest:ok`; the last entry proves the DSH host → plugin autoStart → Python
  FastAPI → HTTP path.
- Real STK end-to-end is covered by the Python product's integration test.

MIT licensed.
