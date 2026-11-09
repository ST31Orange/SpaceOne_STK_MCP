export interface StkErrorShape {
  code: string;
  message: string;
  details?: unknown;
  hint?: string;
  retryable?: boolean;
}

export class StkPluginError extends Error {
  readonly code: string;
  readonly details?: unknown;
  readonly hint?: string;
  readonly retryable: boolean;

  constructor(shape: StkErrorShape) {
    super(shape.message);
    this.name = 'StkPluginError';
    this.code = shape.code;
    this.details = shape.details;
    this.hint = shape.hint;
    this.retryable = shape.retryable ?? false;
  }

  toJSON(): StkErrorShape {
    return {
      code: this.code,
      message: this.message,
      ...(this.details === undefined ? {} : { details: this.details }),
      ...(this.hint === undefined ? {} : { hint: this.hint }),
      retryable: this.retryable,
    };
  }
}
