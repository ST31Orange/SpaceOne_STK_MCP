/**
 * spaceone-stk-plugin — DeepSeek Harness native tools for AGI/Ansys STK 11/12.
 *
 * The TypeScript shell never touches COM. Every tool call is an HTTP request to
 * the Python kernel (`spaceone-stk-mcp`), which owns the STK automation apartment.
 *
 * @module spaceone-stk-plugin
 */

import { appendFileSync } from 'node:fs';
import { StkClient, resolveConfig, type StkPluginConfig } from './client.js';
import { createToolDefinitions } from './tools.js';

/** Optional activation trace used by the packaging smoke test. */
function mark(stage: string): void {
  const target = process.env.DSH_STK_PLUGIN_MARKER;
  if (!target) return;
  try {
    appendFileSync(target, `${stage}\n`, 'utf8');
  } catch {
    /* diagnostics must never affect activation */
  }
}

mark('module');

/** Cordis plugin name. */
export const name = 'spaceone-stk-plugin';

/**
 * The tool runtime is mandatory. DSH activates the plugin only once
 * `ctx.tools` exists, which is also what `apply` registers into.
 */
export const inject = ['tools'];

const DSH_TOOLS_PACKAGE = '@deepseek-ai/dsh-tools';

type DefineTool = (options: Record<string, unknown>) => unknown;

/** Registry-compatible local definition builder used when dsh-tools is absent. */
const localDefineTool: DefineTool = (options) => options;

let defineTool: DefineTool = localDefineTool;
let usingFallback = true;
try {
  const module = (await import(DSH_TOOLS_PACKAGE)) as { defineTool?: DefineTool };
  if (typeof module.defineTool === 'function') {
    defineTool = module.defineTool;
    usingFallback = false;
  }
} catch {
  // The fallback definition below is accepted by the registry; this path is
  // used by standalone tests and by hosts that do not expose dsh-tools.
}

function warn(ctx: unknown, message: string): void {
  try {
    const context = ctx as { logger?: ((name: string) => unknown) | { warn?: (msg: string) => void } };
    if (typeof context.logger === 'function') {
      const logger = context.logger('spaceone-stk-plugin') as { warn?: (msg: string) => void };
      logger?.warn?.(message);
      return;
    }
    context.logger?.warn?.(message);
  } catch {
    /* logging must never break activation */
  }
}

function info(ctx: unknown, message: string): void {
  try {
    const context = ctx as { logger?: ((name: string) => unknown) | { info?: (msg: string) => void } };
    if (typeof context.logger === 'function') {
      const logger = context.logger('spaceone-stk-plugin') as { info?: (msg: string) => void };
      logger?.info?.(message);
      return;
    }
    context.logger?.info?.(message);
  } catch {
    /* logging must never break activation */
  }
}

/**
 * Register the STK tools.
 *
 * @param ctx - Cordis host context; must provide `tools`.
 * @param config - plugin row config (`baseUrl`, `autoStart`, `pythonPath`, ...).
 */
export function apply(ctx: { tools: { register: (definition: unknown) => unknown } }, config?: StkPluginConfig): void {
  mark('apply');
  const settings = resolveConfig(config);
  const client = new StkClient(settings);
  const raw = usingFallback;
  const definitions = createToolDefinitions(defineTool, client, raw);

  let registered = 0;
  for (const definition of definitions) {
    try {
      ctx.tools.register(definition);
      registered += 1;
    } catch (error) {
      warn(
        ctx,
        `failed to register a tool: ${error instanceof Error ? error.message : String(error)}`,
      );
    }
  }
  mark(`registered:${registered}:${raw ? 'fallback' : 'dsh-tools'}`);
  info(
    ctx,
    `registered ${registered} STK tools (kernel ${settings.baseUrl}, autoStart=${settings.autoStart}, `
      + `${raw ? 'fallback schema' : 'dsh-tools schema'})`,
  );

  // Packaging smoke test: with DSH_STK_PLUGIN_SELFTEST=1, exercise the full
  // DSH host → HTTP → Python path without requiring a model turn.
  if (process.env.DSH_STK_PLUGIN_SELFTEST === '1') {
    void client
      .call('stk_status', {})
      .then((value) => mark(`selftest:ok:${JSON.stringify(value)}`))
      .catch((error) =>
        mark(
          `selftest:error:${error instanceof Error ? error.message : String(error)}`,
        ),
      );
  }
}
