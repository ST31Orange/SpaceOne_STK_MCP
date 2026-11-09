# 实测记录

测试机器与版本：

- Windows 10/11 x64
- Python 3.12
- STK 11.2.0 / STK 12.2（本机安装）
- Node.js 22 + DSH headless/desktop profile

## 1. Python 单元测试

```text
cd spaceone-stk-mcp
python -m pytest -q
```

结果：

```text
35 passed, 1 skipped in 8.93s
```

覆盖：catalog 唯一性、JSON Schema、时间工具、序列化、名称/路径校验、保存目录安全、HTTP 路由、MCP 握手。

## 2. 真实 STK 集成测试

```powershell
$env:STK_MCP_RUN_INTEGRATION = "1"
python -m pytest -q tests/test_stk_integration.py -s
```

结果：

```text
STK 11.2.0：1 passed in 105.87s
STK 12：    1 passed in 83.84s
```

覆盖：

1. `stk_connect`（自动探测）
2. `scenario_create`（IT_Pytest，1 天）
3. `satellite_create` + `satellite_set_orbit`（7000 km、97.4°、RAAN 10°、M=45°）
4. `satellite_state`（位置/速度/LLA/经典根数）
5. `facility_create`（40°N, 116°E）
6. `access_compute`
7. 覆盖定义 + 经纬度网格 + 资产 + `coverage_compute`
8. `report_create`（Access 报告）
9. `equipment_create` + `equipment_configure` + `equipment_list`
10. `platform_create` + `platform_set_waypoints` + `platform_state`
11. `area_target_set_polygon`
12. `target_set_position`
13. `chain_create` + `chain_compute_access`
14. `report_list_styles`
15. `constellation_build_walker`（6 星、3 面）
16. `astrogator_summary` + `astrogator_run`
17. TLE（SGP4，COM `SetState`；Connect TCP 回退）
18. `scenario_save`（确认 + 专用空目录）→ `scenario_close` → `scenario_open`
19. 保存确认缺失 `SAVE_CONFIRMATION_REQUIRED`
20. 中文保存路径被拒绝
21. 非法规格样式返回 `INVALID_ARGS` + `available_styles`

## 3. CLI 自测

```powershell
spaceone-stk-mcp selftest
```

结果：12/12 步通过。CLI 自测使用独立的临时目录，不触碰用户场景。

## 4. HTTP 内核

```text
GET /health
{"ok":true,"service":"spaceone-stk-mcp","connected":false,"tool_count":77}
```

```text
GET /api/v1/tools
77 个 ToolSpec
```

## 5. MCP stdio 握手

MCP 客户端 `initialize` → `tools/list`（77 个）→ `tools/call stk_status` 返回 `connected:false`，通过。

## 6. DSH 插件测试

```powershell
cd spaceone-stk-plugin
npm test
```

结果：7 passed。覆盖：

- 插件导出 `apply` + `inject: ['tools']`
- 注册 42 个工具
- `stk_list_tools` 的 `direct_tool` / `call_via` 标记
- 结构化 Python 错误映射
- 内核不可达时的可操作错误
- JSON Schema → DSH 参数 DSL

## 7. DSH 实际加载验证

设置 marker 后运行 headless：

```text
module
apply
registered:42:fallback
selftest:ok
```

说明：

- 42 个工具全部注册成功；
- `fallback` 表示 profile 中无法解析 `@deepseek-ai/dsh-tools`，使用本地同签名 `defineTool`；
- `selftest:ok` 证明 **DSH Host → 插件 autoStart → Python FastAPI → HTTP** 链路成功。

## 7b. 真实模型 Function Calling 会话

使用 `stkheadless` + `DEEPSEEK_API_KEY`，由真实模型发起工具调用。

### 第一轮（27 工具版本）

模型调用了场景、卫星、轨道、设备、平台航路、多边形面目标、设施、链访问等工具；当时未精选的 `platform_create`、`area_target_create`、`chain_create` 自动回退到 `stk_call`。结果：设备 1、航路点 2、多边形 4、链区间 1（509.17 s）。

这暴露了“操作名未直接注册”的可用性问题，随后补齐 wrapper。

### 第二轮（直接 wrapper）

模型只用直接工具，连续调用 11 个，全部成功；链区间为 0，因为该会话未给卫星设轨道，模型自行诊断并如实说明。

### 第三轮（覆盖/报告样式，42 工具版本）

模型直接调用 `stk_coverage_stats`（361 行时间序列）和 `stk_report_list_styles(category=Coverage)`（32 个样式）。`stk_report_create(style=Coverage)` 仍返回 `ReportCreate(Coverage): Command has failed`。

根因：`Coverage` 是 `ObjectCoverage` 类下的样式名，不能用于 `CoverageDefinition` 对象；第一版校验只按全局名称匹配，因此放行。随后改为按对象 `ClassName` 过滤允许的样式类别，并新增集成断言：`Cov + style=Coverage` 必须返回 `INVALID_ARGS` 且带 `available_styles`。

### 第四轮（最终可用性验收）

隔离 STK 实例（`STK_MCP_ATTACH_EXISTING=false`，无头），模型只使用直接 `stk_*` 工具，明确禁止保存/关闭/断开：

1. `stk_status`
2. `stk_scenario_create`（PluginUsabilityCheck，1 小时）
3. `stk_constellation_build_walker`（VerifyWalker，6 星 / 3 面）
4. `stk_facility_create`（Beijing）
5. `stk_coverage_create`（Cov1）
6. `stk_coverage_set_grid`（global 10°）
7. `stk_coverage_add_asset`（Sat01）
8. `stk_coverage_compute`
9. `stk_coverage_stats`
10. `stk_report_list_styles`

结果：**10/10 成功**；Walker 6 星；覆盖 61 行（首点 3.9753%，末点累计 27.9860%）；报告样式 32 个；场景保持打开、未保存、未关闭、未断开。

## 8. DSH 插件 autoStart 验证

独立 Node 脚本：

```js
apply(ctx, { baseUrl: 'http://127.0.0.1:18081', autoStart: true, serverPort: 18081 });
await tools.stk_status.execute({}, {});
```

结果：插件自动启动 `python -m spaceone_stk_mcp.cli serve-http --port 18081`；测试后按端口找到 PID 并停止，无残留。

## 9. 有头/无头与保存安全

默认：

- `STK_MCP_VISIBLE=true`
- `STK_MCP_USER_CONTROL=true`
- 正常任务结束后不自动关闭场景、不主动退出 STK
- `stk_connect(visible=false)` 可在不重建场景的情况下切无头

保存：

- 默认不自动保存；
- `scenario_save` 必须 `confirm_save=true`；
- 路径必须是 ASCII；
- 不传路径时保存到 `Documents\STK 11 (x64)\<name>\<name>.sc`（STK 12 对应目录）；
- 保存目录必须为空或只包含该场景自己的 `Catalog` / `.sc3` / sidecar 文件；存在无关文件时返回 `UNSAFE_SAVE_DIRECTORY`；
- 场景目录超过 `STK_MCP_MAX_SAVE_BYTES`（默认 2 GB）时返回 `SAVE_TOO_LARGE`；
- 已用单元测试覆盖“拒绝无关文件目录”和“超限大小检测”，未在真实用户目录里做大文件保存测试。

## 10. 未验证/边界

- **STK 12 全量回归**：已通过 83.84 s；默认仍优先 STK 11。
- **3D/2D 窗口视觉验证**：`scenario_set_view` 只做窗口激活，未做截图/像素断言。
- **Astrogator**：只有 summary / RunMCS；Targeter、段编辑未封装。
- **CommSystem**：STK 11 COM 的 `Transmitters.AddObject` 拒绝外部 Tx/Rx，未封装半可用工具。
- **保存**：保守策略要求专用空目录；已有场景目录只允许该场景自己的 sidecar 文件。

## 11. 清理测试痕迹

- 测试用 `stkheadless` profile 已删除，仅保留 `desktop`；
- 测试 STK 进程、Python 内核、8080/5001 监听已清理；
- `spaceone-stk-mcp` 为 editable 安装，版本 1.0.0。
