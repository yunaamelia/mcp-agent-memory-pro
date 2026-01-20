export class MemoryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MemoryError';
  }
}

export class DatabaseError extends MemoryError {
  constructor(
    message: string,
    public cause?: Error
  ) {
    super(message);
    this.name = 'DatabaseError';
  }
}

export class VectorStoreError extends MemoryError {
  constructor(
    message: string,
    public cause?: Error
  ) {
    super(message);
    this.name = 'VectorStoreError';
  }
}

export class EmbeddingServiceError extends MemoryError {
  constructor(
    message: string,
    public statusCode?: number
  ) {
    super(message);
    this.name = 'EmbeddingServiceError';
  }
}

export class ValidationError extends MemoryError {
  constructor(
    message: string,
    public field?: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends MemoryError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`);
    this.name = 'NotFoundError';
  }
}
