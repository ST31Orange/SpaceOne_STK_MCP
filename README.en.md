# SpaceOne_STK_MCP

**An LLM tool Agent for space mission simulation**: wraps the full AGI/Ansys STK 11/12 capability into 77 atomic operations, curates 42 function-calling tools, and lets a large language model drive STK purely through natural language — scenario building, constellation design, coverage/access analysis, and report export.

```
┌──────────────────────────────┐        ┌──────────────────────────────┐
│ DeepSeek Harness (DSH)        │        │ Claude / Cursor / any MCP    │
│  spaceone-stk-plugin (TS)     │        │  spaceone-stk-mcp stdio      │
│  ctx.tools.register(...)      │        │  77 MCP tools                │
└──────────────┬───────────────┘        └──────────────┬───────────────┘
               │ fetch HTTP /api/v1/tools/{name}       │ stdio JSON-RPC
               ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Python kernel spaceone-stk-mcp                                        │
│  FastAPI (127.0.0.1:8080)  +  MCP server  +  77-op registry          │
│  StkSession → single-thread STA COM → pywin32 → STK 11/12            │
└─────────────────────────────────────────────────────────────────────┘
```

## Two products, one kernel

| Product | Directory | Form | For |
|---|---|---|---|
| **SpaceOne STK MCP kernel** | [`stk-mcp/`](stk-mcp/) (dist name `spaceone-stk-mcp`) | Python package: MCP stdio server + FastAPI REST kernel + CLI | Any MCP client / HTTP caller |
| **SpaceOne STK DSH plugin** | [`spaceone-stk-plugin/`](spaceone-stk-plugin/) | DSH native plugin: TypeScript shell + HTTP client | Function calling inside DeepSeek Harness |

Both share the same Python STK kernel but are packaged, configured and installed independently. The TypeScript side never calls STK COM directly (no `winax`); all COM calls happen on a single COM apartment thread inside the Python process.

## Highlights

- **77 atomic operations**: scenario, satellite/orbit (classical, Cartesian, TLE, ephemeris), facility/place/area target, sensor, antenna/receiver/transmitter/radar, aircraft/ship/ground-vehicle route, constellation, chain, coverage/FOM, access/constraint, data providers, reports, animation, raw Connect.
- **42 direct tools**: 40 curated high-frequency operations + `stk_call` (all 77 operations) + `stk_list_tools` (catalog), registered into DSH with the `stk_*` prefix.
- **STK 11/12 auto-detection** (STK 11 preferred); force with `STK_MCP_PROG_ID` / `STK_MCP_PREFERRED_VERSION`.
- **Headed and interactive by default**: `STK_MCP_VISIBLE=true`, `STK_MCP_USER_CONTROL=true`; switch to headless with `stk_connect(visible=false)` without losing the scenario.
- **Scenario stays open**: normal tasks do not close the scenario or quit STK; do not use `stk_disconnect` as a finish step.
- **Save requires confirmation**: `scenario_save` needs `confirm_save=true` and an ASCII-only path; default path is `Documents\STK 11 (x64)\<name>\<name>.sc` (or `Documents\STK 12`). The save directory must be new/empty or dedicated to this scenario (`UNSAFE_SAVE_DIRECTORY`), and the folder size limit is 2 GB (`SAVE_TOO_LARGE`).
- **Fully verified**: real STK 11.2.0 integration tests pass; DSH headless loads the plugin and registers 42 tools.

## Layout

```text
SpaceOne_STK_MCP\
├─ README.md                       # this file
├─ docs\
│  ├─ INSTALL.md                   # Windows install/uninstall
│  ├─ ARCHITECTURE.md              # layering, COM, HTTP, error model
│  ├─ DSH_CONFIG.md                # DSH profile / cordis.patch.yml / TOML
│  ├─ TOOL_CATALOG.md              # 77-operation catalog (generated)
│  └─ VERIFICATION.md              # verification log and commands
│
├─ stk-mcp\                        # Product 1: kernel (dist: spaceone-stk-mcp)
│  ├─ pyproject.toml
│  ├─ README.md / README.en.md
│  ├─ contracts\tools.json         # language-neutral 77-op JSON Schema
│  ├─ src\spaceone_stk_mcp\
│  │  ├─ config.py / errors.py / timeutil.py / serialization.py
│  │  ├─ com_worker.py             # single-thread COM apartment
│  │  ├─ session.py                # STK connection / version / lifecycle
│  │  ├─ enums.py / stk_common.py
│  │  ├─ tooling.py / registry.py  # declarative op registry
│  │  ├─ operations\               # 77 ops by domain
│  │  ├─ http_server.py            # FastAPI REST kernel (8080)
│  │  ├─ mcp_server.py             # MCP stdio server
│  │  ├─ selftest.py               # end-to-end STK self-test
│  │  └─ cli.py                    # serve-mcp / serve-http / selftest / doctor
│  ├─ tests\
│  ├─ examples\
│  └─ scripts\
│
└─ spaceone-stk-plugin\            # Product 2: DSH plugin
   ├─ package.json                 # name: spaceone-stk-plugin
   ├─ cordis.patch.yml             # DSH mount entry
   ├─ config.example.toml          # equivalent TOML config
   ├─ tsconfig.json
   ├─ src\
   │  ├─ index.ts                  # apply(ctx, config) + inject: ['tools']
   │  ├─ client.ts                 # fetch HTTP / auto-start kernel
   │  ├─ schema.ts                 # JSON Schema → DSH defineTool DSL
   │  ├─ tools.ts                  # 40 curated tools + stk_call + stk_list_tools
   │  └─ generated\catalog.ts      # generated from the Python registry
   ├─ lib\                         # tsc output (loaded by DSH)
   ├─ test\
   └─ locale\ / icon.svg
```

## Quick start

### 1. Install the Python kernel

```powershell
cd D:\DSH_AI\DSH_STK_MCP\stk-mcp
python -m pip install -e .
python -m spaceone_stk_mcp.cli doctor
python -m spaceone_stk_mcp.cli selftest
```

### 2A. Use as an MCP server

```json
{
  "mcpServers": {
    "spaceone-stk-mcp": {
      "command": "python",
      "args": ["-m", "spaceone_stk_mcp.mcp_server"],
      "env": { "STK_MCP_PROG_ID": "STK11.Application" }
    }
  }
}
```

### 2B. Use as a DSH plugin (one-click from the DSH Plugins UI)

In the DSH **Plugins** page, "Install from source" with either:

- **npm package name** (published to npm):
  ```text
  spaceone-stk-plugin
  ```
- **GitHub Release tarball URL**:
  ```text
  https://github.com/ST31Orange/SpaceOne_STK_MCP/releases/download/v1.0.0/spaceone-stk-plugin-1.0.2.tgz
  ```

Restart DSH (or open a new session) — the plugin registers **42 `stk_*` tools**.

> **The plugin bundles the Python kernel**: `spaceone-stk-plugin` ships offline kernel wheels
> inside the npm package (`vendor/wheels`). On the first `stk_*` call, if the kernel is missing
> from the configured Python environment, the plugin **auto-installs it offline from the bundled
> wheels** (no internet, no PyPI needed), then starts the kernel. The bundled wheels target
> **Python 3.12 x64**.

> UI install is the same as `dsh plugin add <source>` (DSH forwards to pnpm):
>
> ```powershell
> dsh plugin --profile desktop add "spaceone-stk-plugin"
> # or
> dsh plugin --profile desktop add "https://github.com/ST31Orange/SpaceOne_STK_MCP/releases/download/v1.0.0/spaceone-stk-plugin-1.0.2.tgz"
> ```
>
> Behind an intranet proxy you may need `$env:NODE_OPTIONS="--use-system-ca"` first.

**Note**: the plugin is only the shell — the target machine still needs the Python kernel
(step 1, the `spaceone-stk-mcp` package). For offline machines use the LAN kit in `dist/`
(see below).

The plugin connects to `http://127.0.0.1:8080`; with `autoStart=true` the first call runs:

```powershell
python -m spaceone_stk_mcp.cli serve-http --port 8080
```

See [`docs/DSH_CONFIG.md`](docs/DSH_CONFIG.md).

## Verification status

| Item | Result |
|---|---|
| Python unit tests | 35 passed |
| Real STK 11.2.0 integration | 1 passed (~106 s) |
| Real STK 12 integration | 1 passed (~84 s) |
| CLI `spaceone-stk-mcp selftest` | 12/12 steps |
| HTTP `/api/v1/stk/test` | `passed=true`, 12 steps (~52 s) |
| DSH headless plugin load | `registered:42:fallback` + `selftest:ok` |
| Real DSH model session | 11 direct `stk_*` calls OK |
| Plugin Node tests | 7 passed |

> Both STK 11 (11.2.0) and STK 12.2 are installed here; STK 11 is the default. Switch with `STK_MCP_PROG_ID=STK12.Application`.

## Design notes

1. **Why HTTP instead of COM in TS**: COM uses the Windows apartment model; the DSH Node process is not suited to hold STK proxies. Python serializes all COM calls on one STA thread to avoid `RPC server unavailable`. TS only handles schema, HTTP, timeout, auto-start and error mapping.
2. **`defineTool` and JSON Schema**: the plugin uses DSH's `defineTool` when `@deepseek-ai/dsh-tools` resolves; otherwise a same-signature local `defineTool` registers standard JSON Schema directly (`registered:42:fallback`). Python does the final argument validation either way.
3. **One contract, one kernel**: `stk-mcp/contracts/tools.json` is the single source of truth; `export_catalog.py` generates the plugin catalog so schemas never drift.

## Known limitations

- Windows only; STK must be a locally installed automation object.
- TLE / `FromFile` prefer COM `SetState`, fall back to STK Connect TCP (5001). The Connect port is process-global: when STK 11 and 12 run together, TCP may land on another instance, so TLE prefers COM.
- Reports use `ReportCreate`; style availability depends on the STK license and installed modules.
- Advanced modules (Astrogator targeter, CommSystem, radar, EOIR, SEET) are not fully wrapped; extend via `stk_execute_command` / `stk_call`.
- Coverage stats are sampled/summarized; use `coverage_stats` or `data_provider_query` for full point data.

## Docs

- [Install](docs/INSTALL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [DSH config](docs/DSH_CONFIG.md)
- [77-op catalog](docs/TOOL_CATALOG.md)
- [Verification](docs/VERIFICATION.md)
- [Kernel README](stk-mcp/README.en.md)
- [Plugin README](spaceone-stk-plugin/README.en.md)
