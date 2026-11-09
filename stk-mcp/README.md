# spaceone-stk-mcp

用 Python + `win32com` 控制本地 **AGI/Ansys STK 11/12** 的完整工具集。同一套操作通过三种方式暴露：

- **MCP stdio 服务器**：Claude Desktop、Cursor、Claude Code、任意 MCP 客户端；
- **FastAPI REST 内核**：默认 `127.0.0.1:8080`，供 DSH 插件或其他程序调用；
- **Python 库 / CLI**：脚本、批处理、自测与诊断。

> TypeScript 侧不直接调用 STK COM。所有 COM 调用都发生在 Python 进程的单一 STA 线程中。

## 特性

- **77 个操作**：场景、卫星与轨道、设施/地点/面目标（椭圆/多边形）、传感器、天线/接收机/发射机/雷达、飞机/舰船/车辆航路、星座、链、覆盖与 FOM、访问与约束、数据提供器、报告、动画、原始 Connect。
- **STK 11/12 自动适配**：默认优先 STK 11，可用环境变量强制版本。
- **真实 STK 验证**：场景创建、经典轨道、传播、状态、访问、覆盖、报告、TLE、保存/重开均已在本机 STK 11.2.0 上跑通。
- **默认有头、可交互**：新建 STK 默认 `visible=true`、`user_control=true`；可用 `stk_connect(visible=false)` 按次切无头，不丢场景。
- **场景默认保留**：正常建模/分析后不自动关闭场景、不主动调用 `Quit`；不要用 `stk_disconnect` 收尾，让用户自己关闭。由自动化启动的实例在最后一个 COM 引用释放后可能自行退出，因此请保持 Python 内核运行。
- **保存需确认**：默认不自动保存；`scenario_save` 必须 `confirm_save=true`，路径必须为 ASCII（禁止中文）。不传路径时保存到 STK 默认目录（`Documents\STK 11 (x64)\<name>\<name>.sc` 或 STK 12 对应目录）。保存目录必须是新空目录或只包含该场景自己的 sidecar 文件；有无关文件拒绝，超过 2 GB 报 `SAVE_TOO_LARGE`。
- **COM 线程安全**：FastAPI/MCP 的并发请求被串行化到同一个 COM apartment 线程。
- **端到端自测**：`spaceone-stk-mcp selftest` 或 `POST /api/v1/stk/test` 自动创建临时场景并验证 12 个步骤。
- **契约驱动**：`contracts/tools.json` 是 MCP / REST / DSH 插件共享的语言无关契约。

## 安装

要求：Windows、Python ≥ 3.10、本机安装并授权 STK 11 或 12。

```powershell
cd D:\DSH_AI\DSH_spaceone_stk_mcp\spaceone-stk-mcp
python -m pip install -e .
python -m spaceone_spaceone_stk_mcp.cli doctor
```

建议使用虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## 快速开始

### 1. 自测（会启动 STK）

```powershell
python -m spaceone_spaceone_stk_mcp.cli selftest
```

输出 12 个步骤：连接、创建场景、创建卫星、经典轨道+传播、状态查询、设施、访问、访问报告、覆盖、覆盖统计、保存、清理。

### 2. 启动 REST 内核

```powershell
python -m spaceone_spaceone_stk_mcp.cli serve-http --host 127.0.0.1 --port 8080
# 或
python -m uvicorn spaceone_stk_mcp.http_server:app --port 8080
```

浏览器打开 <http://127.0.0.1:8080/docs> 查看 OpenAPI。

### 3. 启动 MCP 服务器

```powershell
python -m spaceone_spaceone_stk_mcp.mcp_server
# 或
spaceone-stk-mcp serve-mcp
```

MCP 客户端配置（Claude Desktop 示例）：

```json
{
  "mcpServers": {
    "spaceone-stk-mcp": {
      "command": "python",
      "args": ["-m", "spaceone_spaceone_stk_mcp.mcp_server"],
      "env": {
        "spaceone_stk_mcp_PROG_ID": "STK11.Application",
        "spaceone_stk_mcp_VISIBLE": "true"
      }
    }
  }
}
```

Claude Code / `.mcp.json`：

```json
{
  "mcpServers": {
    "spaceone-stk-mcp": {
      "command": "python",
      "args": ["-m", "spaceone_spaceone_stk_mcp.mcp_server"]
    }
  }
}
```

## CLI

```text
spaceone-stk-mcp serve-mcp                  # MCP stdio（默认）
spaceone-stk-mcp serve-http --port 8080     # REST 内核
spaceone-stk-mcp list-tools [--json]        # 列出 77 个操作
spaceone-stk-mcp catalog                    # 机器可读完整目录
spaceone-stk-mcp call <tool> --args '{...}' # 命令行调用一个操作
spaceone-stk-mcp selftest                   # 真实 STK 端到端自测
spaceone-stk-mcp doctor                     # Python/pywin32/STK ProgID/Connect 检查
```

示例：

```powershell
spaceone-stk-mcp call scenario_create --args '{"name":"Demo","start_time":"1 Jan 2026 00:00:00.000","stop_time":"2 Jan 2026 00:00:00.000"}'
spaceone-stk-mcp call satellite_create --args '{"name":"Sat1","propagator":"TwoBody"}'
spaceone-stk-mcp call satellite_set_orbit --args '{"satellite_name":"Sat1","mode":"classical","semi_major_axis_km":7000,"eccentricity":0.001,"inclination_deg":97.4,"raan_deg":10,"arg_of_perigee_deg":0,"mean_anomaly_deg":45}'
spaceone-stk-mcp call access_compute --args '{"from_object":"Sat1","to_object":"Fac"}'
```

## 有头/无头与场景保存

### 默认有头

```powershell
# 默认：STK 窗口可见、用户可交互
$env:spaceone_stk_mcp_VISIBLE = "true"
$env:spaceone_stk_mcp_USER_CONTROL = "true"
python -m spaceone_spaceone_stk_mcp.cli serve-http
```

按次切到无头（不丢场景）：

```json
{ "visible": false, "user_control": false }
```

调用 `stk_connect` 时传上述参数即可；如果已经连接，它只改窗口模式，不会重建场景。

### 不自动关场景

正常建模/分析结束后**不要调用** `stk_disconnect`。场景保持打开，用户自己在 STK 里关闭。需要显式断开时才用：

```json
{ "quit": true, "close_scenario": true }
```

### 保存要确认 + ASCII 路径

创建场景默认不保存。保存必须显式确认：

```json
{
  "path": "C:\\STK\\scenarios\\mission.sc",
  "confirm_save": true
}
```

不传 `path` 时保存到 STK 默认目录：

```text
C:\Users\<user>\Documents\STK 11 (x64)\<scenario>\<scenario>.sc
```

STK 12 对应 `Documents\STK 12`。路径中出现中文或其他非 ASCII 字符会被拒绝：

```text
INVALID_ARGS: Scenario save path must be ASCII-only (no Chinese characters)
```

模型应先询问用户是否保存、保存到哪里，再传 `confirm_save=true`。

## REST API

统一响应：

```json
{ "ok": true, "tool": "scenario_create", "data": { }, "elapsed_ms": 12.3 }
```

错误：

```json
{
  "ok": false,
  "error": {
    "code": "STK_NOT_CONNECTED",
    "message": "Not connected to STK",
    "retryable": true
  }
}
```

主要端点：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 轻量健康检查（不强制连接 STK） |
| GET | `/api/v1/version` | 产品/STK/工具数量 |
| GET | `/api/v1/tools` | 77 操作目录（含 schema） |
| GET | `/api/v1/tools/{name}` | 单个操作 schema |
| POST | `/api/v1/tools/{name}` | 调用操作，body `{"arguments": {...}}` |
| POST | `/api/v1/call` | 通用调用，body `{"name": "...", "arguments": {...}}` |
| POST | `/api/v1/session/connect` | 连接 STK |
| DELETE | `/api/v1/session` | 释放连接（可选 quit/close_scenario） |
| GET/POST/DELETE | `/api/v1/scenario` | 场景信息/创建/关闭 |
| GET | `/api/v1/objects` | 对象列表 |
| POST | `/api/v1/access` | 访问计算 |
| POST | `/api/v1/coverage` | 覆盖计算 |
| POST | `/api/v1/stk/test` | 端到端自测 |

示例：

```powershell
$body = @{ arguments = @{ name = "Demo"; start_time = "1 Jan 2026 00:00:00.000"; stop_time = "2 Jan 2026 00:00:00.000" } } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/api/v1/tools/scenario_create -ContentType application/json -Body $body

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/api/v1/stk/test -TimeoutSec 300
```

## 配置

所有配置通过环境变量或 `.env`：

| 变量 | 默认 | 说明 |
|---|---|---|
| `spaceone_stk_mcp_PROG_ID` | `auto` | `STK11.Application` / `STK12.Application` / `auto` |
| `spaceone_stk_mcp_PREFERRED_VERSION` | `11` | `auto` 时优先版本 |
| `spaceone_stk_mcp_VISIBLE` | `true` | 新建实例是否显示 GUI（默认有头） |
| `spaceone_stk_mcp_USER_CONTROL` | `true` | 是否允许用户操作 STK |
| `spaceone_stk_mcp_ATTACH_EXISTING` | `true` | 优先附着已运行实例 |
| `spaceone_stk_mcp_AUTO_CONNECT` | `true` | 首次工具调用自动连接 |
| `spaceone_stk_mcp_QUIT_ON_DISCONNECT` | `false` | disconnect 是否退出 STK |
| `spaceone_stk_mcp_CLOSE_SCENARIO_ON_DISCONNECT` | `false` | disconnect 是否关闭场景 |
| `spaceone_stk_mcp_HOST` / `spaceone_stk_mcp_PORT` | `127.0.0.1` / `8080` | REST 监听 |
| `spaceone_stk_mcp_API_KEY` | 空 | 设置后要求 `X-API-Key` |
| `spaceone_stk_mcp_REQUEST_TIMEOUT` | `180` | 单次 COM 操作预算（秒） |
| `spaceone_stk_mcp_MAX_ROWS` | `20000` | 数据表最大行数 |
| `spaceone_stk_mcp_MAX_SAVE_BYTES` | `2000000000` | 场景目录保存上限（字节），超过报 `SAVE_TOO_LARGE` |
| `spaceone_stk_mcp_CONNECT_HOST` / `PORT` | `127.0.0.1` / `5001` | STK Connect TCP |
| `spaceone_stk_mcp_LOG_LEVEL` | `INFO` | 日志级别 |

完整示例见 [`.env.example`](.env.example)。

## 操作目录

77 个操作按领域分组：

| 分类 | 代表操作 |
|---|---|
| connection | `stk_connect`, `stk_disconnect`, `stk_status`, `stk_capabilities`, `stk_execute_command`, `stk_selftest` |
| scenario | `scenario_create`, `scenario_open`, `scenario_save`, `scenario_close`, `scenario_info`, `scenario_set_time` |
| satellite | `satellite_create`, `satellite_set_orbit`, `satellite_propagate`, `satellite_state`, `satellite_ephemeris`, `satellite_tle_summary` |
| objects | `object_list`, `object_info`, `facility_create`, `place_create`, `area_target_set_polygon`, `target_set_position` |
| sensor / constellation / chain | `sensor_create`, `constellation_create`, `constellation_build_walker`, `chain_compute_access` |
| equipment | `equipment_create`, `equipment_list`, `equipment_delete`, `equipment_configure` |
| platform | `platform_create`, `platform_set_waypoints`, `platform_state`, `platform_list` |
| astrogator | `astrogator_summary`, `astrogator_run` |
| coverage | `coverage_create`, `coverage_set_grid`, `coverage_add_asset`, `coverage_compute`, `coverage_fom_create` |
| access | `access_compute`, `access_batch`, `access_report`, `access_set_constraint` |
| data / report | `data_provider_list`, `data_provider_query`, `report_list_styles`, `report_create` |
| animation / graphics | `animation_control`, `animation_info`, `object_set_graphics` |

完整表格（JSON Schema 见 [`contracts/tools.json`](contracts/tools.json)）：[`../docs/TOOL_CATALOG.md`](../docs/TOOL_CATALOG.md)。

## 架构

```text
MCP client ──stdio──┐
                    ├─→ 统一操作注册表（77 ToolSpec）→ StkSession
HTTP client ────────┘                                  │
                                                       ▼
                                        ComWorker（单线程 STA）
                                                       │
                                                       ▼
                                     pywin32 → STK 11/12 COM
```

- `tooling.py`：声明式 `ToolSpec`；MCP、HTTP、catalog 共用。
- `session.py`：ProgID 探测、版本识别、附着/启动、断开、原始命令。
- `com_worker.py`：一个长生命周期线程 + `COINIT_APARTMENTTHREADED`；嵌套调用内联执行，避免死锁。
- `stk_common.py`：对象解析、数据提供器、访问区间、报告、约束。
- `serialization.py`：COM SAFEARRAY/DataSets/tuple/时间 → JSON。
- `selftest.py`：临时场景的全链路验证。

更多：[`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)。

## 测试

```powershell
# 单元测试（不启动 STK）
python -m pytest -q

# 真实 STK 集成测试（会启动 STK）
$env:spaceone_stk_mcp_RUN_INTEGRATION="1"
python -m pytest -q tests/test_stk_integration.py -s
```

本机实测：35 个单元测试通过；真实 STK 11.2.0 集成测试 1 passed（约 106 s），STK 12 约 84 s。

## 示例

- [`examples/basic_scenario.py`](examples/basic_scenario.py)：Python 服务直接建场景、卫星、轨道、状态。
- [`examples/coverage_region.py`](examples/coverage_region.py)：区域覆盖 + FOM + 统计。
- [`examples/http_client.py`](examples/http_client.py)：纯 HTTP 调用 REST 内核。

## 已知限制

- 仅 Windows；Linux/macOS 只能做 catalog/离线测试。
- TLE / `FromFile` 优先走 COM `SetState`，失败才回退 STK Connect TCP（默认 5001）；若同时运行多个 STK 版本，Connect 端口可能指向另一个实例，因此 COM 是首选。
- 报告依赖 `ReportCreate` 与已安装的 STK 报告样式。
- 设备配置：`Simple Receiver Model` 的 `Frequency/Bandwidth` 在 STK 中是只读属性，工具会把它们放进 `errors`；`GOverT` 可写。Radar 模型配置未封装。
- `platform_set_waypoints` 使用 time-specified great-arc，至少需要 2 个航路点；`target_set_position` 的 spherical 第三参数沿用 STK 的高度语义。
- `satellite_tle_summary` 只对 SGP4/TLE 卫星有数据；TwoBody 卫星返回空表。
- 高级模块（Astrogator 目标器、CommSystem、雷达、EOIR、SEET）未逐一封装；用 `stk_execute_command` 扩展。
- `chain_compute_access` 目前返回计算完成状态；链的逐 strand 区间受 STK COM 暴露限制，可用报告或 `data_provider_query` 补充。
- 覆盖 FOM 的 `definition_type` 使用 STK 枚举索引；不同 STK 版本可用类型以 `supported_types` 返回为准。

## License

MIT。
