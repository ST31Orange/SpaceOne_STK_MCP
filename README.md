# SpaceOne_STK_MCP

**面向航天任务仿真的大模型工具 Agent**：把 AGI/Ansys STK 11/12 的完整能力封装成 77 个原子操作，再精选出 42 个 Function Calling 工具，让大模型仅凭自然语言即可驱动 STK 完成场景建模、星座设计、覆盖/访问分析与报告导出。

```
┌──────────────────────────────┐        ┌──────────────────────────────┐
│ DeepSeek Harness (DSH)        │        │ Claude / Cursor / 任意 MCP   │
│  spaceone-stk-plugin (TS)     │        │  spaceone-stk-mcp stdio      │
│  ctx.tools.register(...)      │        │  77 个 MCP tools             │
└──────────────┬───────────────┘        └──────────────┬───────────────┘
               │ fetch HTTP /api/v1/tools/{name}       │ stdio JSON-RPC
               ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Python 内核 spaceone-stk-mcp                                          │
│  FastAPI (127.0.0.1:8080)  +  MCP server  +  统一操作注册表 (77 ops) │
│  StkSession → 单线程 STA COM apartment → pywin32 → STK 11/12        │
└─────────────────────────────────────────────────────────────────────┘
```

## 两套产品，一个内核

| 产品 | 目录 | 形态 | 面向 |
|---|---|---|---|
| **SpaceOne STK MCP 内核** | [`stk-mcp/`](stk-mcp/)（发行名 `spaceone-stk-mcp`） | Python 包：MCP stdio 服务器 + FastAPI REST 内核 + CLI | 任意 MCP 客户端 / HTTP 调用方 |
| **SpaceOne STK DSH 插件** | [`spaceone-stk-plugin/`](spaceone-stk-plugin/) | DSH 原生插件：TypeScript 外壳 + HTTP 客户端 | DeepSeek Harness 对话中的 Function Calling |

两套产品共享同一个 Python STK 内核，但打包、配置、安装方式完全独立。TypeScript 侧从不直接调用 STK COM，也不依赖 `winax`；所有 COM 调用都发生在 Python 进程的单一 COM apartment 线程中。

## 核心能力

- **77 个原子操作**：场景、卫星/轨道（经典根数、笛卡尔、TLE、星历文件）、设施/地点/面目标（椭圆/多边形）、传感器、天线/接收机/发射机/雷达、飞机/舰船/车辆航路、星座、链、覆盖/FOM、访问/约束、数据提供器、报告、动画、原始 Connect。
- **42 个直接工具**：40 个精选高频操作 + `stk_call`（调用全部 77 个操作）+ `stk_list_tools`（发现操作），以 `stk_*` 前缀注册到 DSH。
- **STK 11/12 自动适配**，默认优先 STK 11；可用 `STK_MCP_PROG_ID` / `STK_MCP_PREFERRED_VERSION` 强制版本。
- **默认有头、可交互**：`STK_MCP_VISIBLE=true`、`STK_MCP_USER_CONTROL=true`；可用 `stk_connect(visible=false)` 切到无头，且不丢失场景。
- **场景默认保留**：正常建模/分析后不自动关闭场景、不主动退出 STK；不要用 `stk_disconnect` 收尾，让用户自己关闭。
- **保存需确认**：默认不自动保存；`scenario_save` 必须 `confirm_save=true`，路径必须是 ASCII（禁止中文）。不传路径时保存到 STK 默认目录 `Documents\STK 11 (x64)\<name>\<name>.sc`（STK 12 对应 `Documents\STK 12`）。保存目录必须是新空目录或该场景自己的目录；有无关文件会拒绝（`UNSAFE_SAVE_DIRECTORY`），超过 2 GB 会报 `SAVE_TOO_LARGE`。
- **完整可验证**：真实 STK 11.2.0 集成测试通过；DSH headless 实际加载插件并注册 42 个工具。

## 目录结构

```text
SpaceOne_STK_MCP\
├─ README.md                       # 本文件：产品总览
├─ docs\
│  ├─ INSTALL.md                   # Windows 安装与卸载
│  ├─ ARCHITECTURE.md              # 分层、COM、HTTP 与错误模型
│  ├─ DSH_CONFIG.md                # DSH profile / cordis.patch.yml / TOML 示例
│  ├─ TOOL_CATALOG.md              # 77 个操作总表（自动生成）
│  └─ VERIFICATION.md              # 实测记录与复现命令
│
├─ stk-mcp\                        # 产品一：SpaceOne STK MCP 内核（发行名 spaceone-stk-mcp）
│  ├─ pyproject.toml
│  ├─ README.md / README.en.md
│  ├─ contracts\tools.json         # 语言无关的 77 操作 JSON Schema
│  ├─ src\spaceone_stk_mcp\
│  │  ├─ config.py / errors.py / timeutil.py / serialization.py
│  │  ├─ com_worker.py             # 单线程 COM apartment
│  │  ├─ session.py                # STK 连接/版本/生命周期
│  │  ├─ enums.py / stk_common.py
│  │  ├─ tooling.py / registry.py  # 声明式操作注册表
│  │  ├─ operations\               # 按领域拆分的 77 个操作
│  │  ├─ http_server.py            # FastAPI REST 内核 (8080)
│  │  ├─ mcp_server.py             # MCP stdio 服务器
│  │  ├─ selftest.py               # 端到端 STK 自测
│  │  └─ cli.py                    # serve-mcp / serve-http / selftest / doctor
│  ├─ tests\                       # 单元测试 + 真实 STK 集成测试
│  ├─ examples\
│  └─ scripts\                     # 导出 catalog / 工具文档
│
└─ spaceone-stk-plugin\            # 产品二：SpaceOne STK DSH 插件
   ├─ package.json                 # name: spaceone-stk-plugin
   ├─ cordis.patch.yml             # DSH 实际挂载入口
   ├─ config.example.toml          # 等价 TOML 配置（参考）
   ├─ tsconfig.json
   ├─ src\
   │  ├─ index.ts                  # apply(ctx, config) + inject: ['tools']
   │  ├─ client.ts                 # fetch HTTP / 自动拉起 Python 内核
   │  ├─ schema.ts                 # JSON Schema → DSH defineTool DSL
   │  ├─ tools.ts                  # 40 个精选工具 + stk_call + stk_list_tools
   │  └─ generated\catalog.ts      # 从 Python 注册表生成，避免漂移
   ├─ lib\                         # tsc 构建产物（DSH 实际加载）
   ├─ test\                        # Node 原生测试（mock HTTP）
   └─ locale\ / icon.svg
```

## 5 分钟快速开始

### 1. 安装 Python 内核

```powershell
cd D:\DSH_AI\DSH_STK_MCP\stk-mcp
python -m pip install -e .
python -m spaceone_stk_mcp.cli doctor          # 检查 pywin32 / STK ProgID / Connect 端口
python -m spaceone_stk_mcp.cli selftest        # 启动 STK 并跑 12 步端到端自测
```

### 2A. 作为 MCP 服务器使用

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

### 2B. 作为 DSH 插件使用（DSH 插件界面一键安装）

在 DSH 的 **插件（Plugins）** 界面，从源安装（Install from source），任选其一：

- **npm 包名**（已发布到 npm registry）：
  ```text
  spaceone-stk-plugin
  ```
- **GitHub Release tarball URL**：
  ```text
  https://github.com/ST31Orange/SpaceOne_STK_MCP/releases/download/v1.0.0/spaceone-stk-plugin-1.0.2.tgz
  ```

安装后重启 DSH（或新开会话），插件注册 **42 个 `stk_*` 工具**。

> **插件自带 Python 内核**：`spaceone-stk-plugin` 的 npm 包里内置了内核的离线 wheel
> （`vendor/wheels`）。首次调用某个 `stk_*` 工具时，若检测到目标 Python 环境没有内核，
> 插件会**自动用包内 wheel 离线安装**（无需联网、无需 PyPI），然后启动内核。
> 前提是目标机 Python 为 **3.12 x64**（wheel 按此打包）。

> 界面安装 = `dsh plugin add <源>`（DSH 转发给 pnpm）。命令行等价写法：
>
> ```powershell
> dsh plugin --profile desktop add "spaceone-stk-plugin"
> # 或
> dsh plugin --profile desktop add "https://github.com/ST31Orange/SpaceOne_STK_MCP/releases/download/v1.0.0/spaceone-stk-plugin-1.0.2.tgz"
> ```
>
> 若内网代理导致 TLS 证书错误，先设 `$env:NODE_OPTIONS="--use-system-ca"`。

**重要**：插件只是外壳，目标机还必须有 Python 内核（步骤 1 的 `spaceone-stk-mcp` 包）。离线场景直接用仓库 `dist/` 下的离线包（见下文"离线安装"）。

插件默认连接 `http://127.0.0.1:8080`；若内核未启动且 `autoStart=true`，首次调用会自动执行：

```powershell
python -m spaceone_stk_mcp.cli serve-http --port 8080
```

详细配置见 [`docs/DSH_CONFIG.md`](docs/DSH_CONFIG.md)。

## 实测状态

| 验证项 | 结果 |
|---|---|
| Python 单元测试（catalog/time/serialization/validation/HTTP/MCP handshake） | 35 passed |
| 真实 STK 11.2.0 集成测试（场景/轨道/访问/覆盖/报告/TLE/设备/平台航路/面目标/链/Walker/Astrogator） | 1 passed，约 106 s |
| 真实 STK 12 集成测试（同一套用例） | 1 passed，约 84 s |
| CLI `spaceone-stk-mcp selftest` | 12/12 步通过，约 20 s |
| HTTP `/api/v1/stk/test` | `passed=true`，12 步，约 52 s（含 STK 启动） |
| DSH headless 实际加载插件 | `module` → `apply` → `registered:42:fallback` → `selftest:ok`（含 autoStart + HTTP） |
| DSH 真实模型会话 | 11 个直接 `stk_*` 调用成功；设备 1 / 航路点 2 / 多边形 4 / 链区间 1（含轨道时） |
| DSH 插件 Node 测试 | 7 passed（mock HTTP / Schema 转换 / 错误映射 / autoStart） |

> 本机同时安装 STK 11 与 STK 12.2；产品默认使用 STK 11，已验证 11.2.0。STK 12 的枚举与对象模型在关键路径上兼容，切换见 `STK_MCP_PROG_ID=STK12.Application`。

## 重要设计说明

1. **为什么 DSH 插件走 HTTP，而不是在 TS 里调 COM**
   - COM 是 Windows apartment 模型；DSH 的 Node 进程不适合持有 STK 代理。
   - Python 端用单一 STA 线程串行化所有 COM 调用，避免 `RPC server unavailable`。
   - TS 侧只做 schema、HTTP、超时、自动拉起和错误映射。

2. **`defineTool` 与 JSON Schema**
   - DSH 的 `defineTool` 使用精简 DSL；插件在能解析 `@deepseek-ai/dsh-tools` 时调用它，并把 Python 的 JSON Schema 转成 DSL。
   - 第三方插件在 profile 中通常解析不到该包；此时插件使用**同签名的本地 `defineTool`**，直接把标准 JSON Schema 注册给 `ctx.tools`。DSH 已验证可接受并注册 42 个工具。
   - 两条路径都由 Python 端做最终参数校验。

3. **两套产品，一个内核**
   - `stk-mcp/contracts/tools.json` 是唯一契约。
   - `stk-mcp/scripts/export_catalog.py` 生成 `spaceone-stk-plugin/src/generated/catalog.ts`。
   - 修改 Python 操作后重新生成，TS 侧 schema 不会漂移。

## 已知边界

- 仅 Windows；STK 必须是本机安装的 Desktop/Engine 自动化对象。
- TLE / `FromFile` 优先走 COM `SetState`，失败才回退 STK Connect TCP（默认 5001）。注意 Connect 端口是进程级全局的：同时运行 STK 11 和 12 时，TCP 可能落到另一个实例，TLE 因此优先走 COM。
- 报告使用 `ReportCreate`，可生成 STK 内置样式；报告样式的可用性取决于 STK 许可证与安装模块。
- 高级模块（Astrogator 目标器、CommSystem、雷达、EOIR、SEET 等）未逐一封装；可通过 `stk_execute_command` 或 `stk_call` 扩展。
- 覆盖统计返回的是抽样/摘要；完整逐点数据请用 `coverage_stats` 或 `data_provider_query`。

## 文档索引

- [安装与卸载](docs/INSTALL.md)
- [架构与错误模型](docs/ARCHITECTURE.md)
- [DSH 配置挂载](docs/DSH_CONFIG.md)
- [77 操作目录](docs/TOOL_CATALOG.md)
- [实测记录](docs/VERIFICATION.md)
- [内核产品说明](stk-mcp/README.md)
- [DSH 插件说明](spaceone-stk-plugin/README.md)
