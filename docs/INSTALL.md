# 安装与卸载

本文以 Windows + 本机 STK 11/12 + DeepSeek Harness 为例。两套产品共享 Python 内核，DSH 插件本身不需要编译 STK 相关原生模块。

## 1. 前置检查

```powershell
python --version                 # 3.10+
python -c "import win32com; print('pywin32 ok')"
Get-ChildItem "C:\Program Files\AGI" -Directory
```

应至少看到 `STK 11` 或 `STK 12`。STK 需要本机许可证；没有许可证时 COM 连接会失败。

检查 ProgID：

```powershell
python -m spaceone_stk_mcp.cli doctor
```

`stk_connect_port` 为 `false` 不一定是错误：只有在 STK 正在运行且启用了 Connect 监听时，端口才会打开。默认 STK 11 启动后会监听 5001。

## 2. 安装 Python 内核

推荐虚拟环境，避免污染系统 Python，也避免覆盖你已有的 `spaceone-stk-mcp` 版本：

```powershell
cd D:\DSH_AI\DSH_STK_MCP\spaceone-stk-mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

如果使用系统 Python：

```powershell
python -m pip install -e .
```

> 注意：如果之前用 `pip install -e D:\AIHOME\OpenCode\spaceone-stk-mcp` 安装过同名包，
> 本次安装会卸载旧版本。建议在虚拟环境中安装，或先记录旧版本。

验证：

```powershell
python -m spaceone_stk_mcp.cli list-tools | Select-Object -First 10
python -m spaceone_stk_mcp.cli doctor
```

## 3. 跑通真实 STK

```powershell
python -m spaceone_stk_mcp.cli selftest
```

预期 12 个步骤全部 `ok:true`，最后输出 `"passed": true`。首次会启动 STK，约 20–60 秒。

如果没有通过：

- `STK_CONNECTION_ERROR`：STK 未安装、未授权，或 ProgID 不匹配；设置 `STK_MCP_PROG_ID=STK11.Application` 再试。
- 超时：关闭 STK 的模态对话框，或把 `STK_MCP_REQUEST_TIMEOUT` 调大。
- 报告失败：确认 STK 安装包含 Report 模块与 “Access” 样式。

## 4. 安装 DSH 插件

确认 DSH CLI 可用（未加入 PATH 时使用完整路径）：

```powershell
dsh --version
# 或
& "C:\Users\<you>\AppData\Local\Programs\DeepSeek Harness\resources\runtime\cli\bin\dsh.cmd" --version
```

安装到桌面 profile：

```powershell
dsh plugin --profile desktop add "link:D:\DSH_AI\DSH_STK_MCP\spaceone-stk-plugin"
```

重启 DSH，或至少新开一个会话（插件在 profile 启动时挂载）。

验证 profile 组合：

```powershell
dsh --profile desktop --dump-config | Select-String -Pattern "spaceone-stk-plugin" -Context 2,8
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

## 5. 启动 Python 内核

插件默认 `autoStart=true`，第一次工具调用会自动启动：

```powershell
python -m spaceone_stk_mcp.cli serve-http --host 127.0.0.1 --port 8080
```

也可以手动常驻启动（推荐生产使用）：

```powershell
# 前台
python -m spaceone_stk_mcp.cli serve-http --port 8080

# 后台（PowerShell）
Start-Process -WindowStyle Hidden python -ArgumentList "-m","spaceone_stk_mcp.cli","serve-http","--port","8080"
```

验证：

```powershell
curl.exe http://127.0.0.1:8080/health
```

`connected:false` 是正常的；第一次 `stk_*` 工具调用才会连接 STK。

## 6. 与 DSH 会话验证

在 DSH 新会话里输入：

```text
先调用 stk_status 看 STK 是否已连接；如果没有，调用 stk_connect。
然后创建场景 Demo2026（2026-01-01 到 2026-01-02），
创建卫星 Sat1（7000 km、97.4°、RAAN 10°），传播后报告 ICRF 位置。
```

模型应依次调用 `stk_status` → `stk_connect` → `stk_scenario_create` → `stk_satellite_create` → `stk_satellite_set_orbit` → `stk_satellite_state`。

## 7. 配置覆盖

在 `~/.dsh/profiles/desktop/cordis.patch.yml` 追加（`config` 整体替换）：

```yaml
- id: spaceone-stk-plugin
  config:
    baseUrl: http://127.0.0.1:8080
    autoStart: false
    pythonPath: C:\Users\you\AppData\Local\Programs\Python\Python312\python.exe
    timeoutMs: 300000
    serverPort: 8080
    startupTimeoutMs: 30000
```

详细字段见 [`DSH_CONFIG.md`](DSH_CONFIG.md)。

## 8. 卸载

```powershell
dsh plugin --profile desktop remove spaceone-stk-plugin
python -m pip uninstall spaceone-stk-mcp
```

如果创建了测试 profile：

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.dsh\profiles\stktest"
Remove-Item -Recurse -Force "$env:USERPROFILE\.dsh\profiles\stkheadless"
```

清理运行数据（可选）：

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.spaceone-stk-mcp\reports"
Remove-Item -Recurse -Force "$env:USERPROFILE\.spaceone-stk-mcp\selftest"
```

## 9. 端口与安全

- 默认只绑定 `127.0.0.1`，不暴露到局域网。
- 如果必须跨机访问，设置 `STK_MCP_API_KEY`，并在插件 `apiKey` 中填同一个值；同时用防火墙限制来源。
- `stk_execute_command` 可以执行任意 Connect 命令，属于高权限逃生口；不要向不可信调用方开放。
- 插件不主动杀 Python 内核或 STK 进程；需要时手动停止。

## 10. 常见问题

| 问题 | 处理 |
|---|---|
| `dsh` 命令找不到 | 使用 `...\resources\runtime\cli\bin\dsh.cmd` 完整路径 |
| 插件安装了但工具不出现 | 重启 DSH；确认安装的是当前 `--profile`；查看 profile 的 `package.json` bundles |
| `pythonPath` 指向 venv 但 autoStart 失败 | 改成 venv 的 `python.exe` 绝对路径，并确认该环境装了 `spaceone-stk-mcp` |
| 8080 被占用 | 改 `baseUrl` 与 `serverPort`，或先手动在 18080 启动再改 baseUrl |
| STK 启动很慢 | `STK_MCP_VISIBLE=false`，关闭 splash/许可对话框；首次连接耐心等待 |
| 中文乱码 | 终端用 UTF-8；Python 输出本身是 UTF-8，文件写入使用 `utf-8` |
