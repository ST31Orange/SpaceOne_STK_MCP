import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { after, before, test } from 'node:test';

import { apply } from '../lib/index.js';
import { jsonSchemaToParameterSpec, SUPPORTED_DSL_KEYS } from '../lib/schema.js';
import { CURATED_TOOLS, ALL_TOOLS } from '../lib/generated/catalog.js';

let server;
let baseUrl;
let calls = [];
let failNext = false;

before(async () => {
  server = createServer((req, res) => {
    const json = (status, body) => {
      res.writeHead(status, { 'content-type': 'application/json' });
      res.end(JSON.stringify(body));
    };
    if (req.method === 'GET' && req.url === '/health') {
      return json(200, { ok: true, service: 'spaceone-stk-mcp', connected: false, tool_count: ALL_TOOLS.length });
    }
    if (req.method === 'GET' && req.url === '/api/v1/tools') {
      return json(200, { ok: true, data: { tool_count: ALL_TOOLS.length, tools: ALL_TOOLS } });
    }
    if (req.method === 'POST' && req.url?.startsWith('/api/v1/tools/')) {
      let body = '';
      req.on('data', (chunk) => (body += chunk));
      req.on('end', () => {
        const operation = decodeURIComponent(req.url.split('/').pop());
        const args = body ? JSON.parse(body).arguments : {};
        calls.push({ operation, args });
        if (failNext) {
          failNext = false;
          return json(422, {
            ok: false,
            error: { code: 'STK_OPERATION_ERROR', message: 'simulated failure', retryable: false },
          });
        }
        return json(200, { ok: true, data: { operation, args } });
      });
      return;
    }
    return json(404, { ok: false, error: { code: 'NOT_FOUND', message: 'not found' } });
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  baseUrl = `http://127.0.0.1:${address.port}`;
});

after(() => server?.close());

function registerTools(config = {}) {
  const registered = [];
  const ctx = { tools: { register: (definition) => registered.push(definition) } };
  apply(ctx, { baseUrl, autoStart: false, timeoutMs: 5000, ...config });
  return registered;
}

test('registers curated tools plus generic call and catalog', () => {
  calls = [];
  const tools = registerTools();
  assert.equal(tools.length, CURATED_TOOLS.length + 2);
  const names = new Set(tools.map((tool) => tool.name));
  assert.ok(names.has('stk_scenario_create'));
  assert.ok(names.has('stk_call'));
  assert.ok(names.has('stk_list_tools'));
  for (const tool of tools) {
    assert.equal(typeof tool.name, 'string');
    assert.equal(typeof tool.description, 'string');
    assert.equal(typeof tool.parameters, 'object');
    assert.equal(typeof tool.execute, 'function');
    assert.equal(typeof tool.output.render, 'function');
  }
});

test('execute proxies to the Python operation over HTTP', async () => {
  calls = [];
  const tools = registerTools();
  const status = tools.find((tool) => tool.name === 'stk_status');
  const value = await status.execute({}, {});
  assert.deepEqual(value, { operation: 'stk_status', args: {} });
  assert.deepEqual(calls[0], { operation: 'stk_status', args: {} });
});

test('stk_call forwards any operation and its arguments', async () => {
  calls = [];
  const tools = registerTools();
  const generic = tools.find((tool) => tool.name === 'stk_call');
  const value = await generic.execute(
    { operation: 'coverage_compute', arguments: { coverage_name: 'Cov1' } },
    {},
  );
  assert.deepEqual(value, {
    operation: 'coverage_compute',
    args: { coverage_name: 'Cov1' },
  });
});

test('stk_list_tools returns the full operation catalog locally', async () => {
  const tools = registerTools();
  const list = tools.find((tool) => tool.name === 'stk_list_tools');
  const value = await list.execute({}, {});
  assert.equal(value.tool_count, ALL_TOOLS.length);
  assert.equal(value.tools.length, ALL_TOOLS.length);
  assert.equal(value.tools[0].parameters, undefined);
  const withSchema = await list.execute({ include_schema: true }, {});
  assert.equal(typeof withSchema.tools[0].parameters, 'object');
  const coverageStats = value.tools.find((tool) => tool.name === 'stk_coverage_stats');
  assert.equal(coverageStats.direct_tool, true);
  const placeCreate = value.tools.find((tool) => tool.name === 'stk_place_create');
  assert.equal(placeCreate.direct_tool, false);
  assert.equal(placeCreate.call_via, 'stk_call');
});

test('structured Python errors become plugin errors', async () => {
  failNext = true;
  const tools = registerTools();
  const status = tools.find((tool) => tool.name === 'stk_status');
  await assert.rejects(() => status.execute({}, {}), (error) => {
    assert.equal(error.code, 'STK_OPERATION_ERROR');
    assert.equal(error.message, 'simulated failure');
    return true;
  });
});

test('unreachable kernel fails with an actionable code when autoStart is off', async () => {
  const registered = [];
  apply(
    { tools: { register: (definition) => registered.push(definition) } },
    { baseUrl: 'http://127.0.0.1:1', autoStart: false, timeoutMs: 2000 },
  );
  const status = registered.find((tool) => tool.name === 'stk_status');
  await assert.rejects(() => status.execute({}, {}), (error) => {
    assert.equal(error.code, 'STK_KERNEL_NOT_RUNNING');
    assert.match(error.hint, /autoStart|serve-http/);
    return true;
  });
});

test('JSON Schema to DSH DSL conversion uses only supported keys', () => {
  const schema = {
    type: 'object',
    properties: {
      name: { type: 'string', description: 'name', minLength: 1 },
      mode: { type: 'string', enum: ['a', 'b'], default: 'a' },
      list: { type: 'array', items: { type: 'number', minimum: 0 } },
      nested: {
        type: 'object',
        additionalProperties: false,
        properties: { flag: { type: 'boolean' } },
        required: ['flag'],
      },
    },
    required: ['name', 'mode'],
    additionalProperties: false,
  };
  const spec = jsonSchemaToParameterSpec(schema);
  assert.equal(spec.name.required, true);
  assert.equal(spec.mode.required, true);
  assert.deepEqual(spec.mode.enum, ['a', 'b']);
  assert.equal(spec.list.items.type, 'number');
  assert.equal(spec.list.items.minimum, undefined);
  assert.equal(spec.nested.properties.flag.required, true);
  assert.equal(spec.nested.additionalProperties, false);

  const assertKeys = (node) => {
    for (const key of Object.keys(node)) {
      assert.ok(SUPPORTED_DSL_KEYS.has(key), `unsupported DSL key: ${key}`);
    }
    if (node.properties) {
      for (const child of Object.values(node.properties)) assertKeys(child);
    }
    if (node.items) assertKeys(node.items);
    if (node.oneOf) for (const child of node.oneOf) assertKeys(child);
  };
  for (const node of Object.values(spec)) assertKeys(node);
});
