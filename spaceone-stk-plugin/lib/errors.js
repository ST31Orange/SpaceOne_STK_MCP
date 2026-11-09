export class StkPluginError extends Error {
    code;
    details;
    hint;
    retryable;
    constructor(shape) {
        super(shape.message);
        this.name = 'StkPluginError';
        this.code = shape.code;
        this.details = shape.details;
        this.hint = shape.hint;
        this.retryable = shape.retryable ?? false;
    }
    toJSON() {
        return {
            code: this.code,
            message: this.message,
            ...(this.details === undefined ? {} : { details: this.details }),
            ...(this.hint === undefined ? {} : { hint: this.hint }),
            retryable: this.retryable,
        };
    }
}
