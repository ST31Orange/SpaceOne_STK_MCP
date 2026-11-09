import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { StkPluginError } from './errors.js';
/** Directory inside the plugin package that carries the Python kernel wheels. */
const VENDOR_WHEELS = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'vendor', 'wheels');
const DEFAULTS = {
    baseUrl: 'http://127.0.0.1:8080',
    apiKey: '',
    timeoutMs: 180_000,
    autoStart: true,
    pythonPath: 'python',
    serverHost: '127.0.0.1',
    serverPort: 8080,
    startupTimeoutMs: 30_000,
};
function portFromUrl(url) {
    try {
        const parsed = new URL(url);
        if (parsed.port)
            return Number(parsed.port);
        return parsed.protocol === 'https:' ? 443 : 80;
    }
    catch {
        return DEFAULTS.serverPort;
    }
}
export function resolveConfig(config) {
    const input = config && typeof config === 'object' ? config : {};
    const baseUrl = (input.baseUrl || DEFAULTS.baseUrl).replace(/\/+$/, '');
    return {
        baseUrl,
        apiKey: input.apiKey || process.env.STK_MCP_API_KEY || '',
        timeoutMs: Number(input.timeoutMs ?? DEFAULTS.timeoutMs),
        autoStart: input.autoStart ?? DEFAULTS.autoStart,
        pythonPath: input.pythonPath || process.env.STK_MCP_PYTHON || DEFAULTS.pythonPath,
        serverHost: input.serverHost || '127.0.0.1',
        serverPort: Number(input.serverPort ?? portFromUrl(baseUrl)),
        startupTimeoutMs: Number(input.startupTimeoutMs ?? DEFAULTS.startupTimeoutMs),
    };
}
export class StkClient {
    config;
    startPromise = null;
    constructor(config) {
        this.config = config;
    }
    headers() {
        const headers = { 'content-type': 'application/json' };
        if (this.config.apiKey)
            headers['x-api-key'] = this.config.apiKey;
        return headers;
    }
    async request(path, init = {}, timeoutMs = this.config.timeoutMs) {
        const signal = AbortSignal.timeout(Math.max(1_000, timeoutMs));
        let response;
        try {
            response = await fetch(`${this.config.baseUrl}${path}`, {
                ...init,
                headers: { ...this.headers(), ...init.headers },
                signal,
            });
        }
        catch (error) {
            throw new StkPluginError({
                code: 'STK_KERNEL_UNREACHABLE',
                message: `Cannot reach the STK Python kernel at ${this.config.baseUrl}: ${error instanceof Error ? error.message : String(error)}`,
                hint: 'Start it with `python -m spaceone_stk_mcp.cli serve-http --port 8080` or enable autoStart.',
                retryable: true,
            });
        }
        const text = await response.text();
        let payload;
        try {
            payload = text ? JSON.parse(text) : {};
        }
        catch {
            throw new StkPluginError({
                code: 'STK_KERNEL_BAD_RESPONSE',
                message: `STK kernel returned non-JSON (HTTP ${response.status}): ${text.slice(0, 500)}`,
                retryable: false,
            });
        }
        if (!response.ok) {
            const body = payload;
            throw new StkPluginError({
                code: body.error?.code || `HTTP_${response.status}`,
                message: body.error?.message || `STK kernel request failed with HTTP ${response.status}`,
                details: body.error?.details ?? body,
                hint: body.error?.hint,
                retryable: body.error?.retryable ?? response.status >= 500,
            });
        }
        return payload;
    }
    async health() {
        try {
            return await this.request('/health', { method: 'GET' }, 3_000);
        }
        catch (error) {
            if (error instanceof StkPluginError) {
                return { ok: false, service: 'unreachable', stk: { error: error.message } };
            }
            return { ok: false, service: 'unreachable' };
        }
    }
    async ensureServer() {
        const health = await this.health();
        if (health.ok)
            return;
        if (!this.config.autoStart) {
            throw new StkPluginError({
                code: 'STK_KERNEL_NOT_RUNNING',
                message: `STK kernel is not running at ${this.config.baseUrl}`,
                hint: 'Start the Python server or set autoStart=true in the plugin config.',
                retryable: true,
            });
        }
        if (!this.startPromise) {
            this.startPromise = this.startServer().finally(() => {
                this.startPromise = null;
            });
        }
        await this.startPromise;
    }
    async startServer() {
        await this.ensureKernelInstalled();
        const args = [
            '-m',
            'spaceone_stk_mcp.cli',
            'serve-http',
            '--host',
            this.config.serverHost,
            '--port',
            String(this.config.serverPort),
        ];
        let child;
        try {
            child = spawn(this.config.pythonPath, args, {
                detached: true,
                stdio: 'ignore',
                windowsHide: true,
                env: process.env,
            });
        }
        catch (error) {
            throw new StkPluginError({
                code: 'STK_KERNEL_START_FAILED',
                message: `Could not start the STK Python kernel with ${this.config.pythonPath}: ${error instanceof Error ? error.message : String(error)}`,
                hint: 'Install spaceone-stk-mcp into that Python environment or set pythonPath in the plugin config.',
            });
        }
        child.unref();
        const deadline = Date.now() + this.config.startupTimeoutMs;
        while (Date.now() < deadline) {
            await new Promise((resolve) => setTimeout(resolve, 500));
            const health = await this.health();
            if (health.ok)
                return;
        }
        throw new StkPluginError({
            code: 'STK_KERNEL_START_TIMEOUT',
            message: `STK kernel did not become healthy within ${this.config.startupTimeoutMs} ms`,
            hint: `Check that \`${this.config.pythonPath} -m spaceone_stk_mcp.cli serve-http --port ${this.config.serverPort}\` runs.`,
            retryable: true,
        });
    }
    /**
     * Make sure the Python kernel package is installed in the configured Python
     * environment before trying to start the server.
     *
     * Strategy:
     *   1. Probe: `import spaceone_stk_mcp` → already installed, done.
     *   2. Offline install from the wheels bundled inside this plugin
     *      (`vendor/wheels`): `pip install --no-index --find-links <dir> spaceone-stk-mcp`.
     *      This works without internet and without PyPI.
     *   3. Fallback: try online `pip install spaceone-stk-mcp` (needs PyPI).
     *   4. On failure raise a clear STK_KERNEL_MISSING error.
     */
    async ensureKernelInstalled() {
        const probe = await this.runPython(['-c', 'import spaceone_stk_mcp; print("ok")']);
        if (probe.ok)
            return;
        const offline = await this.runPython(['-m', 'pip', 'install', '--no-index', '--find-links', VENDOR_WHEELS, 'spaceone-stk-mcp'], 300_000);
        if (offline.ok) {
            const probe2 = await this.runPython(['-c', 'import spaceone_stk_mcp; print("ok")']);
            if (probe2.ok)
                return;
        }
        // Bundled wheels may not match the target Python (they are cp312 win_amd64).
        const online = await this.runPython(['-m', 'pip', 'install', 'spaceone-stk-mcp'], 300_000);
        if (online.ok) {
            const probe3 = await this.runPython(['-c', 'import spaceone_stk_mcp; print("ok")']);
            if (probe3.ok)
                return;
        }
        throw new StkPluginError({
            code: 'STK_KERNEL_MISSING',
            message: `The spaceone-stk-mcp Python kernel is not installed in the configured Python environment ` +
                `(${this.config.pythonPath})`,
            details: {
                pythonPath: this.config.pythonPath,
                bundledWheels: VENDOR_WHEELS,
                offlinePipOutput: offline.outputTail,
                onlinePipOutput: online.outputTail,
            },
            hint: `Install it manually with: \`${this.config.pythonPath} -m pip install spaceone-stk-mcp\`. ` +
                'The bundled wheels target Python 3.12 x64; on another Python version use the LAN kit wheels, then retry.',
        });
    }
    /**
     * Run a short Python command and capture its output. Used to probe and to
     * install the kernel package. Resolves with ok=true when the exit code is 0.
     */
    async runPython(args, timeoutMs = 120_000) {
        return await new Promise((resolve) => {
            let child;
            try {
                child = spawn(this.config.pythonPath, args, {
                    windowsHide: true,
                    stdio: ['ignore', 'pipe', 'pipe'],
                });
            }
            catch (error) {
                resolve({
                    ok: false,
                    code: null,
                    outputTail: String(error instanceof Error ? error.message : error),
                });
                return;
            }
            let out = '';
            const keepTail = (chunk) => {
                out = (out + String(chunk)).slice(-2000);
            };
            child.stdout?.on('data', keepTail);
            child.stderr?.on('data', keepTail);
            const timer = setTimeout(() => {
                child.kill();
                resolve({ ok: false, code: null, outputTail: out.slice(-800) });
            }, timeoutMs);
            child.on('close', (code) => {
                clearTimeout(timer);
                resolve({ ok: code === 0, code, outputTail: out.slice(-800) });
            });
            child.on('error', (error) => {
                clearTimeout(timer);
                resolve({ ok: false, code: null, outputTail: String(error.message) });
            });
        });
    }
    async call(operation, args = {}) {
        await this.ensureServer();
        const path = `/api/v1/tools/${encodeURIComponent(operation)}`;
        try {
            const payload = await this.request(path, {
                method: 'POST',
                body: JSON.stringify({ arguments: args }),
            });
            if (payload.ok === false || payload.error) {
                throw new StkPluginError({
                    code: payload.error?.code || 'STK_TOOL_ERROR',
                    message: payload.error?.message || `STK operation ${operation} failed`,
                    details: payload.error?.details,
                    hint: payload.error?.hint,
                    retryable: payload.error?.retryable ?? false,
                });
            }
            return payload.data;
        }
        catch (error) {
            if (error instanceof StkPluginError && error.code === 'STK_KERNEL_UNREACHABLE') {
                // A server that died between health and call is restarted once.
                this.startPromise = null;
                const health = await this.health();
                if (!health.ok) {
                    await this.ensureServer();
                    const payload = await this.request(path, {
                        method: 'POST',
                        body: JSON.stringify({ arguments: args }),
                    });
                    return payload.data;
                }
            }
            throw error;
        }
    }
    async listTools() {
        const payload = await this.request('/api/v1/tools', { method: 'GET' });
        return payload.data;
    }
}
