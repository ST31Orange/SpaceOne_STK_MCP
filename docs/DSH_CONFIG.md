# DSH 配置挂载

## 1. 先明确：DSH 当前用 `cordis.patch.yml`，不是 `config.toml`

DSH 的 profile 由 `package.json` 的 `dsh.profile.bundles` + 多层 `cordis.patch.yml` 组合。插件包通过 `package.json` 的 `dsh.bundle.patch` 指向自己的 patch，profile 安装该包后自动插入插件行。

`config.toml` 仅作为**等价配置参考**（见 `spaceone-stk-plugin/config.example.toml`），当前 DSH 不读取它。

## 2. 插件自带挂载行

`spaceone-stk-plugin/cordis.patch.yml`：

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

`package.json`：

```json
{
  "name": "spaceone-stk-plugin",
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } }
}
```

安装：

```powershell
dsh plugin --profile desktop add "link:D:\DSH_AI\DSH_STK_MCP\spaceone-stk-plugin"
```

## 3. profile 覆盖

编辑 `~/.dsh/profiles/desktop/cordis.patch.yml`：

```yaml
- id: spaceone-stk-plugin
  config:
    baseUrl: http://127.0.0.1:8080
    autoStart: true
    pythonPath: C:\Users\you\AppData\Local\Programs\Python\Python312\python.exe
    timeoutMs: 300000
    serverHost: 127.0.0.1
    serverPort: 8080
    startupTimeoutMs: 30000
```

注意事项：

- `config` 是**整体替换**，不是深合并；覆盖时把需要的字段都写上。
- profile 层在 bundle 层之后应用，因此能覆盖插件默认值。
- 修改后重启 DSH，或新开会话。

## 4. 字段说明

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `baseUrl` | string | `http://127.0.0.1:8080` | Python 内核地址；末尾斜杠会被去掉 |
| `apiKey` | string | `""` | 内核设置 `STK_MCP_API_KEY` 时必填，作为 `X-API-Key` |
| `timeoutMs` | number | `180000` | 单次工具调用超时；覆盖/报告可调大 |
| `autoStart` | boolean | `true` | 健康检查失败时自动启动 Python 内核 |
| `pythonPath` | string | `python` | 安装有 `spaceone-stk-mcp` 的 Python 解释器 |
| `serverHost` | string | `127.0.0.1` | 自动启动监听地址 |
| `serverPort` | number | `8080` | 自动启动端口；应与 `baseUrl` 端口一致 |
| `startupTimeoutMs` | number | `30000` | 等待 `/health` 通过的时间 |

## 5. 三种运行模式

### A. 插件自动拉起（默认）

```yaml
autoStart: true
baseUrl: http://127.0.0.1:8080
```

首次工具调用时：

1. `GET /health`；
2. 失败则 `spawn(pythonPath, ['-m','spaceone_stk_mcp.cli','serve-http','--host',...,'--port',...])`；
3. 每 500ms 轮询 `/health`，最多 `startupTimeoutMs`；
4. 成功后执行工具。

Python 内核以 detached 子进程运行；插件退出不会杀死它，后续会话可复用。

### B. 手动常驻（生产推荐）

```powershell
python -m spaceone_stk_mcp.cli serve-http --host 127.0.0.1 --port 8080
```

```yaml
autoStart: false
baseUrl: http://127.0.0.1:8080
```

便于统一管理日志、API key、端口和进程生命周期。

### C. 独立端口

```powershell
python -m spaceone_stk_mcp.cli serve-http --port 18080
```

```yaml
autoStart: false
baseUrl: http://127.0.0.1:18080
serverPort: 18080
```

`serverPort` 只在 autoStart 时使用；手动模式下以 `baseUrl` 为准。

## 6. 等价 `config.toml`

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

再次强调：当前 DSH 不会读取此 TOML；它只是配置语义参考，或供其他 TOML 宿主使用。

## 7. 验证挂载

```powershell
# 组合后的 profile 中应出现插件行
dsh --profile desktop --dump-config | Select-String -Pattern "spaceone-stk-plugin" -Context 2,10
```

应看到：

```yaml
- id: spaceone-stk-plugin
  name: spaceone-stk-plugin
  config:
    baseUrl: http://127.0.0.1:8080
    autoStart: true
    pythonPath: python
    timeoutMs: 180000
```

如果想不污染主 profile 做验证：

```powershell
dsh plugin --profile stkheadless --from-default-profile headless
dsh plugin --profile stkheadless add "link:D:\DSH_AI\DSH_STK_MCP\spaceone-stk-plugin"
# 设置 marker 后启动，验证插件 apply 是否执行
$env:DSH_STK_PLUGIN_MARKER="$env:TEMP\stk-marker.txt"
dsh --profile stkheadless headless "hello"
Get-Content "$env:TEMP\stk-marker.txt"
# 期望：module / apply / registered:42:fallback
```

> headless 需要可用的模型凭据；没有凭据时会在插件挂载后报 `MISSING_CREDENTIAL`，但 marker 仍能证明插件加载与注册。

## 8. API Key

内核：

```powershell
$env:STK_MCP_API_KEY = "your-secret"
python -m spaceone_stk_mcp.cli serve-http --port 8080
```

插件：

```yaml
- id: spaceone-stk-plugin
  config:
    apiKey: your-secret
```

健康检查也受保护时，插件会在请求头带 `X-API-Key`。未设置 key 时不需要该字段。

## 9. 端口冲突排查

```powershell
Get-NetTCPConnection -LocalPort 8080 -State Listen
```

- 如果被其他程序占用，改内核端口 + `baseUrl` + `serverPort`；
- 如果被旧的 `spaceone_stk_mcp` 进程占用，先停止旧进程；
- 浏览器打开 `http://127.0.0.1:8080/health`，应返回 `{"ok":true,"service":"spaceone-stk-mcp",...}`。

## 10. 卸载

```powershell
dsh plugin --profile desktop remove spaceone-stk-plugin
```

然后重启 DSH。Python 内核与 STK 进程不会自动退出；需要时手动停止。
