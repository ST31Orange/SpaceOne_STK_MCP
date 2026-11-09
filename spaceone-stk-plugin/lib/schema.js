/**
 * Convert the canonical JSON Schema produced by the Python catalog into the
 * author-facing schema DSL consumed by DSH's `defineTool`.
 *
 * DSH's DSL supports a deliberately small vocabulary. Constraints that it does
 * not encode (minimum/maximum/pattern/...) are enforced by the Python kernel,
 * so they are intentionally dropped here instead of making the plugin fail to
 * load.
 */
const ANNOTATIONS = ['description', 'title', 'default', 'examples'];
const VALUE_KEYS = ['type', 'enum', 'const', 'items', 'properties', 'additionalProperties', 'oneOf'];
function isRecord(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function toValueSpec(node) {
    const output = {};
    for (const key of ANNOTATIONS) {
        if (node[key] !== undefined)
            output[key] = node[key];
    }
    if (Array.isArray(node.oneOf)) {
        const branches = node.oneOf.filter(isRecord).map((branch) => toValueSpec(branch));
        if (branches.length >= 2) {
            output.oneOf = branches;
            return output;
        }
    }
    const type = typeof node.type === 'string' ? node.type : undefined;
    if (type === 'object') {
        output.type = 'object';
        const properties = isRecord(node.properties) ? node.properties : {};
        const required = new Set(Array.isArray(node.required) ? node.required.map(String) : []);
        const compiled = {};
        for (const [name, value] of Object.entries(properties)) {
            if (!isRecord(value))
                continue;
            const child = toValueSpec(value);
            if (required.has(name))
                child.required = true;
            compiled[name] = child;
        }
        output.properties = compiled;
        output.additionalProperties = node.additionalProperties === true;
        return output;
    }
    if (type === 'array') {
        output.type = 'array';
        output.items = isRecord(node.items) ? toValueSpec(node.items) : { type: 'json' };
        return output;
    }
    if (type === 'string' ||
        type === 'number' ||
        type === 'integer' ||
        type === 'boolean' ||
        type === 'null' ||
        type === 'json') {
        output.type = type;
    }
    else {
        // Unions or unknown shapes remain unconstrained JSON.
        output.type = 'json';
    }
    if (Array.isArray(node.enum))
        output.enum = node.enum;
    if (node.const !== undefined)
        output.const = node.const;
    return output;
}
/** Convert an object-rooted JSON Schema into a DSH parameter property map. */
export function jsonSchemaToParameterSpec(schema) {
    const properties = isRecord(schema.properties) ? schema.properties : {};
    const required = new Set(Array.isArray(schema.required) ? schema.required.map(String) : []);
    const spec = {};
    for (const [name, value] of Object.entries(properties)) {
        if (!isRecord(value))
            continue;
        const child = toValueSpec(value);
        if (required.has(name))
            child.required = true;
        spec[name] = child;
    }
    return spec;
}
/** All keys emitted by the converter, used by the unit tests. */
export const SUPPORTED_DSL_KEYS = new Set([...ANNOTATIONS, ...VALUE_KEYS, 'required']);
