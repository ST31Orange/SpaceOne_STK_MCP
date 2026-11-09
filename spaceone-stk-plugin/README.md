# spaceone-stk-plugin

DeepSeek Harness 原生 STK 插件：**TypeScript 外壳 + Python 内核**。大模型在对话中通过 Function Calling 调用 `stk_*` 工具；TypeScript 侧只发 HTTP 请求，所有 STK COM 调用都在 Python 进程内完成。

- 注册 **42 个工具**：40 个高频精选 + `stk_call`（调用全部 77 个操作）+ `stk_list_tools`（发现操作）。
- 默认连接 `http://127.0.0.1:8080` 的 spaceone-stk-mcp FastAPI 内核。
- 内核未启动且 `autoStart=true` 时，首次工具调用自动执行 `python -m spaceone_spaceone_stk_mcp.cli serve-http`。
- 已用 DSH headless 实测加载：`module → apply → registered:42`。

## 前置条件

1. Windows + 本机安装并授权的 STK 11 或 12。
2. Python 3.10+，已安装 Python 内核：

   ```powershell
   cd D:\DSH_AI\DSH_spaceone_stk_mcp\spaceone-stk-mcp
   python -m pip install -e .
   python -m spaceone_spaceone_stk_mcp.cli doctor
   ```

3. DSH 当前 profile（通常 `desktop` 或 `web`）。

## 安装

### 本地开发安装（推荐）

```powershell
dsh plugin --profile desktop add "link:D:\DSH_AI\DSH_spaceone_stk_mcp\spaceone-stk-plugin"
```

安装后：

- `~/.dsh/profiles/desktop/package.json` 的 `dsh.profile.bundles` 会包含 `spaceone-stk-plugin`；
- 插件自带的 `cordis.patch.yml` 会插入 `spaceone-stk-plugin` 行；
- 重启 DSH 或新开会话后，工具出现在模型工具列表中。

卸载：

```powershell
dsh plugin --profile desktop remove spaceone-stk-plugin
```

> 如果只想验证而不动当前 profile，可以先用独立 profile：
> `dsh plugin --profile stktest add "link:...\spaceone-stk-plugin"`。
> 测试完成后删除 `~/.dsh/profiles/stktest` 即可。

### 发布包安装

```powershell
dsh plugin --profile desktop add spaceone-stk-plugin
# 或从 GitHub / npm 安装发布版本
```

## 工具面

| DSH 工具 | Python 操作 | 用途 |
|---|---|---|
| `stk_connect` | `stk_connect` | 连接/复用 STK 实例 |
| `stk_status` | `stk_status` | 连接状态、版本、当前场景 |
| `stk_scenario_create` | `scenario_create` | 创建场景 |
| `stk_scenario_info` | `scenario_info` | 场景信息与对象清单 |
| `stk_scenario_set_time` | `scenario_set_time` | 修改时间区间 |
| `stk_satellite_create` | `satellite_create` | 创建卫星 |
| `stk_satellite_set_orbit` | `satellite_set_orbit` | 经典/笛卡尔/TLE/文件轨道 |
| `stk_satellite_state` | `satellite_state` | 位置、速度、LLA、根数 |
| `stk_satellite_ephemeris` | `satellite_ephemeris` | 星历采样/CSV |
| `stk_facility_create` | `facility_create` | 地面站 |
| `stk_sensor_create` | `sensor_create` | 简单锥传感器 |
| `stk_access_compute` | `access_compute` | 访问区间 |
| `stk_coverage_create` | `coverage_create` | 覆盖定义 |
| `stk_coverage_set_grid` | `coverage_set_grid` | 全球/经纬度区域网格 |
| `stk_coverage_add_asset` | `coverage_add_asset` | 添加覆盖资产 |
| `stk_coverage_remove_asset` | `coverage_remove_asset` | 移除覆盖资产 |
| `stk_coverage_compute` | `coverage_compute` | 计算覆盖 + 统计摘要 |
| `stk_coverage_stats` | `coverage_stats` | 覆盖统计/时间序列 |
| `stk_coverage_fom_create` | `coverage_fom_create` | 创建覆盖 FOM |
| `stk_coverage_fom_query` | `coverage_fom_query` | 查询 FOM |
| `stk_coverage_grid_inspector` | `coverage_grid_inspector` | 选点查看覆盖 |
| `stk_data_provider_list` | `data_provider_list` | 数据提供器列表 |
| `stk_data_provider_query` | `data_provider_query` | 任意数据提供器 |
| `stk_report_create` | `report_create` | STK 报告导出 |
| `stk_object_list` | `object_list` | 对象清单 |
| `stk_equipment_create` | `equipment_create` | 创建天线/接收机/发射机/雷达 |
| `stk_equipment_configure` | `equipment_configure` | 配置设备模型参数 |
| `stk_equipment_list` | `equipment_list` | 列出父对象设备 |
| `stk_platform_create` | `platform_create` | 创建飞机/舰船/车辆 |
| `stk_platform_set_waypoints` | `platform_set_waypoints` | 飞机/舰船/车辆航路 |
| `stk_area_target_create` | `area_target_create` | 创建面目标 |
| `stk_area_target_set_polygon` | `area_target_set_polygon` | 多边形面目标 |
| `stk_chain_create` | `chain_create` | 创建链 |
| `stk_chain_compute_access` | `chain_compute_access` | 链访问区间 |
| `stk_constellation_build_walker` | `constellation_build_walker` | Walker Delta/Star 批量建星 |
| `stk_astrogator_summary` | `astrogator_summary` | Astrogator 段列表 |
| `stk_astrogator_run` | `astrogator_run` | 运行 Astrogator MCS |
| `stk_report_list_styles` | `report_list_styles` | 列出可用报告样式 |
| `stk_execute_command` | `stk_execute_command` | 原始 Connect 命令 |
| `stk_selftest` | `stk_selftest` | 端到端 STK 自测 |
| `stk_call` | 任意 | 按操作名调用全部 77 个操作 |
| `stk_list_tools` | 本地 | 返回 77 操作目录；`include_schema=true` 时附带完整 schema |

模型典型用法：

```text
帮我建一个 2026-01-01 的场景，放一颗 7000 km、97.4° 的太阳同步卫星，
再建北京地面站，算未来 24 小时访问，并把 Access 报告导出。
```

模型会依次调用 `stk_scenario_create` → `stk_satellite_create` → `stk_satellite_set_orbit` → `stk_facility_create` → `stk_access_compute` → `stk_report_create`。

## 配置

### 实际 DSH 配置：`cordis.patch.yml`

DSH 当前版本用 profile 的 `cordis.patch.yml` 组合配置，不是 `config.toml`。插件自带默认行（`cordis.patch.yml`）：

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

在 **profile 自己的** `~/.dsh/profiles/desktop/cordis.patch.yml` 中按 id 覆盖：

```yaml
- id: spaceone-stk-plugin
  config:
    baseUrl: http://127.0.0.1:8080
    autoStart: true
    pythonPath: C:\Users\you\AppData\Local\Programs\Python\Python312\python.exe
    timeoutMs: 300000
    serverPort: 8080
    startupTimeoutMs: 30000
```

> `config` 是整体替换，不是深合并；覆盖时把需要的字段都写上。

### 等价 `config.toml`（供 TOML 配置宿主/参考）

```toml
[plugins.stk]
base_url = "http://127.0.0.1:8080"
api_key = ""
timeout_ms = 180000
auto_start = true
python_path = "python"
server_host = "127.0.0.1"
server_port = 8080
startup_timeout_ms = 30000
```

完整说明见 [`config.example.toml`](config.example.toml)。

### 配置字段

| 字段 | 默认 | 说明 |
|---|---|---|
| `baseUrl` | `http://127.0.0.1:8080` | Python 内核地址 |
| `apiKey` | 空 | 内核设置 `spaceone_stk_mcp_API_KEY` 时必须一致，作为 `X-API-Key` 发送 |
| `timeoutMs` | `180000` | 单次工具调用预算 |
| `autoStart` | `true` | 健康检查失败时自动拉起 Python 内核 |
| `pythonPath` | `python` | 安装有 `spaceone-stk-mcp` 的 Python |
| `serverHost` | `127.0.0.1` | 自动启动监听地址 |
| `serverPort` | `8080` | 自动启动端口（应与 baseUrl 端口一致） |
| `startupTimeoutMs` | `30000` | 等待 `/health` 的超时 |

## 手动启动内核

如果不用 `autoStart`，先启动：

```powershell
python -m spaceone_spaceone_stk_mcp.cli serve-http --host 127.0.0.1 --port 8080
```

验证：

```powershell
curl.exe http://127.0.0.1:8080/health
```

Health 返回 `connected:false` 是正常的：STK 连接在第一次工具调用时建立（`spaceone_stk_mcp_AUTO_CONNECT=true`），避免插件加载时卡住 30–60 秒启动 STK。

## 架构

```text
DSH Agent
   │ tool call (stk_scenario_create)
   ▼
spaceone-stk-plugin (TypeScript, Node)
   │ ctx.tools.register(defineTool({...}))
   │ HTTP POST /api/v1/tools/scenario_create
   ▼
spaceone-stk-mcp FastAPI (Python, 127.0.0.1:8080)
   │ registry → StkSession → ComWorker (single STA thread)
   ▼
pywin32 → STK 11/12 COM
```

- **TypeScript 不调用 COM**，没有 `winax`。
- `defineTool`：能解析 `@deepseek-ai/dsh-tools` 时使用其 DSL 编译器；第三方 profile 通常解析不到，插件回退到**同签名本地 `defineTool`**，直接把标准 JSON Schema 注册给 `ctx.tools`。DSH 已实测接受并注册 42 个工具。
- 工具 schema 来自 `src/generated/catalog.ts`，由 `spaceone-stk-mcp/scripts/export_catalog.py` 从 Python 注册表生成，避免两套产品漂移。

## 故障排查

| 现象 | 处理 |
|---|---|
| `STK_KERNEL_UNREACHABLE` | 启动 `python -m spaceone_spaceone_stk_mcp.cli serve-http --port 8080`，或检查 `baseUrl` |
| `STK_KERNEL_START_TIMEOUT` | `pythonPath` 不对，或 Python 环境没装 `spaceone-stk-mcp`；手动运行命令确认 |
| `STK_NOT_CONNECTED` | 内核正常但 STK 未连接；调用 `stk_connect` 或检查 STK 许可证 |
| `STK_CONNECTION_ERROR` | STK 未安装/未授权；先 `python -m spaceone_spaceone_stk_mcp.cli doctor` |
| 工具列表里没有 `stk_*` | 确认插件已安装到当前 profile，并重启 DSH/新开会话 |
| `unknown tool "stk_xxx"` | 该操作未注册为直接工具；用 `stk_list_tools` 看 `direct_tool`，非直接操作走 `stk_call`。覆盖统计等常用操作已补齐为直接工具 |
| `ReportCreate(...): Command has failed` | 先用 `stk_report_list_styles` 按对象类别找精确样式；覆盖分析优先用 `stk_coverage_stats`，不要用 `style=Coverage` |
| 401 | 内核设置了 `spaceone_stk_mcp_API_KEY`，插件配置的 `apiKey` 不一致 |
| 端口冲突 | 改 `baseUrl` + `serverPort`，或先手动起在别的端口 |
| STK 窗口被隐藏 | 默认 `spaceone_stk_mcp_VISIBLE=true`；只有显式 `stk_connect(visible=false)` 或环境变量设为 false 才无头 |
| 场景被关闭/STK 退出 | 不要用 `stk_disconnect` 收尾；保持 Python 内核运行，场景会保留。保存需 `confirm_save=true` |
| `UNSAFE_SAVE_DIRECTORY` | 保存目录里有其他场景/无关文件；换新空目录（如 `C:\STK\mission\mission.sc`），避免把默认目录内容并进场景 |
| `SAVE_TOO_LARGE` | 场景目录超过 `spaceone_stk_mcp_MAX_SAVE_BYTES`（默认 2 GB）；检查无关大文件，不要盲目调大上限 |

## 验证

- Node 测试：`npm test`（7 passed；mock HTTP、schema 转换、错误映射、autoStart）。
- DSH headless 加载：设置 `DSH_STK_PLUGIN_MARKER` 后启动测试 profile，得到
  `module → apply → registered:42:fallback → selftest:ok`；其中 `selftest:ok`
  证明 DSH Host → 插件 autoStart → Python FastAPI → HTTP 全链路成功。
- 真实工具链路：mock/真实 Python 内核上执行 `stk_status`、`stk_call`、`stk_list_tools` 均通过。
- 真实 STK 端到端：由 Python 产品的集成测试覆盖（场景/轨道/访问/覆盖/报告/TLE）。

## 已知限制

- 仅 Windows；STK 必须本机安装。
- 工具调用期间如果 STK 弹模态对话框，会表现为超时；请把 STK 设为 `UserControl=false` 或先处理对话框。
- 高级 STK 模块未逐一封装，用 `stk_call` + `stk_execute_command` 扩展。
- 插件不主动终止 Python 内核；它作为共享服务运行，便于多个 DSH 会话复用。

## License

MIT。
