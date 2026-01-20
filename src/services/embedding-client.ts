import { config } from '../utils/config.js';
import { logger } from '../utils/logger.js';
import { EmbeddingServiceError } from '../utils/errors.js';

interface EmbedSingleResponse {
  embedding: number[];
  dimensions: number;
  model: string;
}

interface EmbedBatchResponse {
  embeddings: number[][];
  dimensions: number;
  count: number;
  model: string;
}

interface HealthResponse {
  status: string;
  model: string;
  dimensions: number;
  version: string;
}

export class EmbeddingClient {
  private baseUrl: string;
  private timeout: number = 30000; // 30 seconds

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || config.embeddingServiceUrl;
  }

  async generateEmbedding(text: string, normalize: boolean = true): Promise<number[]> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}/embed/single`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, normalize }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.text();
        throw new EmbeddingServiceError(
          `Embedding service error: ${response.statusText} - ${error}`,
          response.status
        );
      }

      const data = (await response.json()) as unknown as EmbedSingleResponse;
      return data.embedding;
    } catch (error) {
      if (error instanceof EmbeddingServiceError) {
        throw error;
      }

      if ((error as Error).name === 'AbortError') {
        throw new EmbeddingServiceError('Embedding request timeout');
      }

      logger.error('Failed to generate embedding:', error);
      throw new EmbeddingServiceError('Embedding generation failed');
    }
  }

  async generateEmbeddings(texts: string[], normalize: boolean = true): Promise<number[][]> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout * 2);

      const response = await fetch(`${this.baseUrl}/embed/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ texts, normalize }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.text();
        throw new EmbeddingServiceError(
          `Embedding service error: ${response.statusText} - ${error}`,
          response.status
        );
      }

      const data = (await response.json()) as unknown as EmbedBatchResponse;
      return data.embeddings;
    } catch (error) {
      if (error instanceof EmbeddingServiceError) {
        throw error;
      }

      if ((error as Error).name === 'AbortError') {
        throw new EmbeddingServiceError('Batch embedding request timeout');
      }

      logger.error('Failed to generate embeddings:', error);
      throw new EmbeddingServiceError('Batch embedding generation failed');
    }
  }

  async healthCheck(): Promise<HealthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new EmbeddingServiceError('Health check failed', response.status);
      }

      return (await response.json()) as unknown as HealthResponse;
    } catch {
      throw new EmbeddingServiceError('Cannot connect to embedding service');
    }
  }

  async waitForService(maxAttempts: number = 30, delayMs: number = 1000): Promise<void> {
    logger.info('Waiting for embedding service to be ready...');

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        await this.healthCheck();
        logger.info('Embedding service is ready');
        return;
      } catch {
        if (attempt === maxAttempts) {
          throw new EmbeddingServiceError(
            `Embedding service not available after ${maxAttempts} attempts`
          );
        }
        logger.debug(`Attempt ${attempt}/${maxAttempts} - service not ready, retrying... `);
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
  }
}

export const embeddingClient = new EmbeddingClient();
