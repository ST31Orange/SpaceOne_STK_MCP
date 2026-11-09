# 架构与错误模型

## 1. 两套产品、一个内核

```text
产品一  spaceone-stk-mcp（Python）
   ├─ MCP stdio server        → 77 个 MCP tools
   ├─ FastAPI REST kernel     → POST /api/v1/tools/{name}
   ├─ CLI                     → selftest / doctor / call
   └─ 核心库                   → StkSession + operations

产品二  spaceone-stk-plugin（TypeScript）
   ├─ apply(ctx, config)
   ├─ 42 个 DSH tools（40 精选 + stk_call + stk_list_tools）
   └─ HTTP 客户端 + autoStart
```

`spaceone-stk-mcp/contracts/tools.json` 是唯一契约；`scripts/export_catalog.py` 把它转换成 DSH 插件的 `src/generated/catalog.ts`。因此 MCP、REST、DSH 三端的操作名、描述、JSON Schema 保持一致。

## 2. Python 分层

| 层 | 文件 | 职责 |
|---|---|---|
| 协议层 | `mcp_server.py`, `http_server.py` | 把统一注册表投影成 MCP tools / REST 路由 |
| 注册表 | `tooling.py`, `registry.py` | `ToolSpec`、JSON Schema、参数校验、分发 |
| 操作层 | `operations/*.py` | 77 个原子操作，按领域拆分 |
| 公共对象层 | `stk_common.py` | 对象解析、数据提供器、访问区间、报告、约束 |
| 会话层 | `session.py` | ProgID 探测、连接/断开、版本、原始命令 |
| COM 层 | `com_worker.py` | 单线程 STA apartment、嵌套调用内联 |
| 基础层 | `config.py`, `errors.py`, `timeutil.py`, `serialization.py`, `enums.py` | 配置、错误、时间、序列化、枚举 |

## 3. 为什么必须单线程 COM

STK 的自动化对象是 apartment-bound。FastAPI 的同步端点运行在线程池里，如果每个请求都直接 `Dispatch`/调用 COM 代理，会出现：

- `RPC server unavailable`；
- `Call was rejected by callee`；
- 对象代理在错误的线程被释放。

因此：

1. `ComWorker` 只创建一个长生命周期线程；
2. 该线程执行 `pythoncom.CoInitializeEx(COINIT_APARTMENTTHREADED)`；
3. 所有 `session.run(fn)` 提交到该线程；
4. 插件/操作内部再次调用 `session.run` 时检测到当前就是 worker 线程，**内联执行**，避免单线程 executor 自锁；
5. 进程退出时 `shutdown` 在线程内释放引用并 `CoUninitialize`。

`stk_connect` 启动 STK 约需 20–60 秒，因此 HTTP `health` 不主动连接 STK；连接发生在第一次实际工具调用（`STK_MCP_AUTO_CONNECT=true`）。

## 4. 请求流程

### MCP

```text
MCP client
  → stdio JSON-RPC tools/call
  → mcp_server.call_tool
  → asyncio.to_thread(service.invoke)
  → tooling.invoke: JSON Schema 校验
  → session.ensure_connected()
  → session.run(handler)
  → COM worker
  → JSON 结果 → TextContent
```

### REST

```text
POST /api/v1/tools/access_compute
  body {"arguments": {...}}
  → FastAPI 线程池
  → StkService.invoke
  → 同上
  → {"ok": true, "tool": "...", "data": ..., "elapsed_ms": ...}
```

### DSH

```text
DSH Agent tool call
  → spaceone-stk-plugin 定义的 execute(args)
  → StkClient.ensureServer()（必要时 spawn Python）
  → fetch POST /api/v1/tools/{operation}
  → Python 内核
  → data → DSH tool result
```

## 5. 连接与版本

候选 ProgID：

1. `STK_MCP_PROG_ID` 显式指定；
2. 否则 `STK_MCP_PREFERRED_VERSION`（默认 11）优先；
3. 再尝试 12、13。

连接策略：

- `STK_MCP_ATTACH_EXISTING=true`：先 `GetActiveObject`，失败再 `Dispatch`；
- `false`：`DispatchEx` 强制新实例；
- 附着已有实例时**不修改**其 `Visible/UserControl`，避免把用户正在看的 STK 隐藏；
- 新实例默认 `STK_MCP_VISIBLE=true`、`STK_MCP_USER_CONTROL=true`（有头、可交互）；
- 已连接时 `stk_connect(visible=false)` 只调用 `configure_gui` 切换窗口模式，不重建会话；
- 版本优先从 `app.Path` 解析，再尝试 Connect TCP `GetSTKVersion /` 获取精确 build（如 `STK 11.2.0`）。

保存策略：

- `scenario_create` 默认不保存，只在 STK 内存中建立场景；
- `scenario_save` 必须 `confirm_save=true`，否则返回 `SAVE_CONFIRMATION_REQUIRED`；
- 保存路径必须是 ASCII（拒绝中文/非 ASCII）；不传路径时按 `Documents\STK 11 (x64)\<name>\<name>.sc`（或 STK 12 对应目录）保存；
- 保存目录必须是新空目录或只包含该场景自己的 `Catalog` / `.sc3` / sidecar 文件；有无关文件返回 `UNSAFE_SAVE_DIRECTORY`，避免把默认目录内容合并进场景；
- 场景目录超过 `STK_MCP_MAX_SAVE_BYTES`（默认 2 GB）返回 `SAVE_TOO_LARGE`；
- `scenario_open` 会记录已打开文件路径，后续无路径保存会原地保存。

断开策略：

- 默认 `quit=false`、`close_scenario=false`；只释放 COM 引用，不主动调用 `Quit`；
- 由自动化启动的 STK 在最后一个 COM 引用释放后可能自行退出；需要保留状态时先 `scenario_save`，或保持连接不 disconnect；
- `quit=true` 才 `app.Quit()`；
- `close_scenario=true` 才关闭场景。

## 6. 操作实现要点

- **轨道**：`IAgOrbitStateClassical.AssignClassical(coord, a, e, i, argp, raan, mean_anomaly)`；默认 `J2000=3`；TwoBody 的枚举值是 **7**（不是 1）。
- **状态**：组合 `Cartesian Position` + `Cartesian Velocity` + `LLA State` + `Classical Elements` 四个数据提供器。
- **访问区间**：STK 11 的 `ComputedAccessIntervalTimes` 是集合，`GetInterval(i)` 返回 `(start, stop)` 元组；不能按 `.Item(i)` 访问。
- **覆盖网格**：`AgECvBounds` 中 Global=**1**、LatLonRegion=**6**、LatitudeBounds=2、LatitudeLine=3；早期版本代码把 Global 写成 0、区域写成 3 是错的。
- **覆盖统计**：`Percent Coverage` 等数据提供器没有 `Group` 集合，直接 `Exec()`；`Global Coverage` 有 4 个参数；内核会依次尝试多种 `Exec/ExecSingle` 签名。
- **报告**：`ReportCreate <path> Type Save Style "Access" File "..." AccessObject */Facility/Fac`，通过 COM `ExecuteCommand` 执行；不要使用已废弃的 `Report ... Style ... File`。
- **TLE**：`SetState ... TLE "line1" "line2"` 优先走 COM `ExecuteCommand`；COM 失败才回退 Connect TCP。Connect 端口（5001）是进程级全局的，多个 STK 版本同时运行时 TCP 可能指向另一个实例，因此不要默认优先 TCP。
- **图形**：STK 11 的 `obj.Graphics` 直接暴露 `IsObjectGraphicsVisible`、`LabelVisible`、`MarkerStyle`，没有 `.Attributes`。

## 7. 错误模型

所有错误继承 `StkMcpError`：

```json
{
  "code": "STK_OPERATION_ERROR",
  "message": "human readable",
  "details": { "...": "..." },
  "hint": "actionable next step",
  "retryable": false
}
```

| code | HTTP | 含义 |
|---|---|---|
| `INVALID_ARGS` | 400 | JSON Schema 校验失败 / 未知工具 |
| `OBJECT_NOT_FOUND` | 404 | 对象不存在 |
| `STK_NOT_CONNECTED` | 503 | 未连接且 autoConnect 关闭 |
| `STK_CONNECTION_ERROR` | 503 | ProgID/许可证/COM 初始化失败 |
| `STK_OPERATION_ERROR` | 422 | STK 拒绝操作 |
| `STK_COM_ERROR` | 422 | pywin32 COM 错误（带 HRESULT） |
| `CAPABILITY_UNAVAILABLE` | 501 | 功能/许可证/传输不可用 |
| `STK_TIMEOUT` | 504 | COM 操作超时 |

MCP 侧把错误放进 `TextContent` 的 JSON（`{"ok": false, "error": ...}`）；DSH 侧把 `error` 转成 `StkPluginError`，保留 code/hint/retryable。

## 8. DSH `defineTool` 的两条路径

DSH 的 `defineTool` 使用精简 schema DSL，并要求 `output { schema, render }`。第三方插件安装在 profile 的 `node_modules` 中，通常无法解析 `@deepseek-ai/dsh-tools`。因此：

```ts
let defineTool = localDefineTool;
try {
  const mod = await import('@deepseek-ai/dsh-tools');
  defineTool = mod.defineTool ?? localDefineTool;
} catch { /* fallback */ }
```

- **可用时**：`schema.ts` 把标准 JSON Schema 转成 DSH DSL（丢掉 DSH 不支持的 `minimum/maximum/pattern` 等约束），由 `defineTool` 编译并做参数校验。
- **不可用时**：`localDefineTool` 原样返回 registry-ready 定义，`parameters` 是标准 JSON Schema；DSH registry 已验证接受并注册 42 个工具。
- 两条路径最终都由 Python 的 `jsonschema` 再次校验，避免模型参数绕过。

## 9. 并发与性能

- 所有 STK COM 操作串行；并发请求排队，不会破坏 STK 状态。
- 数据表默认上限 20000 行；`satellite_ephemeris` 默认 2000 行。
- 覆盖/报告可能耗时较长；DSH 插件 `timeoutMs` 默认 180 秒，可用配置调大。
- `stk_list_tools` 是本地操作，不访问 HTTP，适合先发现再 `stk_call`。

## 10. 扩展方式

新增一个操作：

1. 在 `spaceone-stk-mcp/src/spaceone_stk_mcp/operations/<domain>.py` 写 handler；
2. 用 `@tool(name, description, object_schema(...), category=..., mutating=...)` 注册；
3. 在 `spaceone-stk-mcp/scripts/export_catalog.py` 的 `CURATED` 中按需加入 DSH 精选；
4. 运行 `python spaceone-stk-mcp/scripts/export_catalog.py`；
5. `cd spaceone-stk-plugin && npm run build`；
6. 重跑单元/集成测试。

TypeScript 侧不需要为新操作改代码：`stk_call` 可以调用任意 Python 操作；只有需要成为“精选工具”时才加入 `CURATED`。
