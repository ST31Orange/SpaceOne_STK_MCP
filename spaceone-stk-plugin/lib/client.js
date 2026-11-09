import { spawn } from 'node:child_process';
import { StkPluginError } from './errors.js';
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
