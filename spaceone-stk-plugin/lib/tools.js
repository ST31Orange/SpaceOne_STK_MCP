import { ALL_TOOLS, CURATED_TOOLS } from './generated/catalog.js';
import { jsonSchemaToParameterSpec } from './schema.js';
function output(raw) {
    return {
        schema: raw ? {} : { type: 'json' },
        render: (_args, value) => [
            { type: 'text', text: typeof value === 'string' ? value : JSON.stringify(value, null, 2) },
        ],
    };
}
function renderTool(tool, client) {
    return async (args) => client.call(tool.operation, args);
}
/** Build the real `defineTool` arguments (DSH schema DSL). */
function dshOptions(tool, client) {
    return {
        name: tool.name,
        description: tool.description,
        parameters: jsonSchemaToParameterSpec(tool.parameters),
        output: output(false),
        timeoutMs: client.config.timeoutMs + 5_000,
        isConcurrencySafe: () => !tool.mutating,
        execute: renderTool(tool, client),
    };
}
/** Build a registry-ready definition without importing DSH's schema compiler. */
function fallbackDefinition(tool, client) {
    return {
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters,
        output: output(true),
        timeoutMs: client.config.timeoutMs + 5_000,
        isConcurrencySafe: () => !tool.mutating,
        execute: renderTool(tool, client),
    };
}
function genericCallDefinition(client, raw) {
    const operationNames = ALL_TOOLS.map((tool) => tool.operation).join(', ');
    const parameters = raw
        ? {
            type: 'object',
            properties: {
                operation: {
                    type: 'string',
                    description: `Python operation name. One of: ${operationNames}`,
                },
                arguments: {
                    type: 'object',
                    description: 'Arguments object for that operation',
                    additionalProperties: true,
                },
            },
            required: ['operation'],
            additionalProperties: false,
        }
        : {
            operation: {
                type: 'string',
                required: true,
                description: `Python operation name. One of: ${operationNames}`,
            },
            arguments: {
                type: 'object',
                additionalProperties: true,
                properties: {},
                description: 'Arguments object for that operation',
            },
        };
    return {
        name: 'stk_call',
        description: 'Call any STK operation by its Python operation name. Use stk_list_tools to discover '
            + 'operation names and their JSON schemas, then pass the arguments object.',
        parameters,
        output: output(raw),
        timeoutMs: client.config.timeoutMs + 5_000,
        isConcurrencySafe: () => false,
        execute: async (args) => {
            const operation = String(args.operation || '');
            const operationArgs = args.arguments && typeof args.arguments === 'object'
                ? args.arguments
                : {};
            return client.call(operation, operationArgs);
        },
    };
}
function listToolsDefinition(raw) {
    const directNames = new Set(CURATED_TOOLS.map((tool) => tool.name));
    return {
        name: 'stk_list_tools',
        description: `List the complete STK operation catalog (${ALL_TOOLS.length} operations) with categories. `
            + 'Only entries with direct_tool=true may be called as tools directly; all others must be '
            + 'invoked through stk_call with their operation name. Set include_schema=true to include '
            + 'each operation\'s full JSON Schema (larger result).',
        parameters: raw
            ? {
                type: 'object',
                properties: {
                    include_schema: {
                        type: 'boolean',
                        description: 'Include full JSON Schema for every operation',
                        default: false,
                    },
                },
                additionalProperties: false,
            }
            : {
                include_schema: {
                    type: 'boolean',
                    description: 'Include full JSON Schema for every operation',
                    default: false,
                },
            },
        output: output(raw),
        timeoutMs: 15_000,
        isConcurrencySafe: () => true,
        execute: async (args) => {
            const includeSchema = args.include_schema === true;
            return {
                tool_count: ALL_TOOLS.length,
                tools: ALL_TOOLS.map((tool) => ({
                    name: tool.name,
                    operation: tool.operation,
                    category: tool.category,
                    mutating: tool.mutating,
                    direct_tool: directNames.has(tool.name),
                    call_via: directNames.has(tool.name) ? 'direct' : 'stk_call',
                    description: tool.description,
                    ...(includeSchema ? { parameters: tool.parameters } : {}),
                })),
            };
        },
    };
}
/**
 * Build every registration for the plugin. When DSH's `defineTool` is
 * available it compiles the schema DSL and wraps argument validation; the
 * fallback path returns the registry-compatible definition directly so the
 * plugin also loads in test harnesses and older hosts.
 */
export function createToolDefinitions(defineTool, client, raw) {
    const definitions = [];
    for (const tool of CURATED_TOOLS) {
        const options = raw ? fallbackDefinition(tool, client) : dshOptions(tool, client);
        definitions.push(defineTool ? defineTool(options) : options);
    }
    for (const options of [genericCallDefinition(client, raw), listToolsDefinition(raw)]) {
        definitions.push(defineTool ? defineTool(options) : options);
    }
    return definitions;
}
export { ALL_TOOLS, CURATED_TOOLS };
