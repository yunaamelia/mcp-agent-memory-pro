import { jest, describe, it, expect, beforeAll, afterAll } from '@jest/globals';
import { handleStoreMemory } from '../../src/tools/store.js';
import { initializeDatabase, closeDatabase } from '../../src/storage/database.js';
import { initializeVectorStore } from '../../src/storage/vector-store.js';
import { MemoryType, MemorySource } from '../../src/types/memory.js';

import { embeddingClient } from '../../src/services/embedding-client.js';

// Spy on embedding client
jest.spyOn(embeddingClient, 'generateEmbedding').mockResolvedValue(new Array(384).fill(0.1));

describe('Store Memory Tool', () => {
  beforeAll(async () => {
    await initializeDatabase();
    await initializeVectorStore();
  });

  afterAll(() => {
    closeDatabase();
  });

  it('should store a valid memory', async () => {
    const result = await handleStoreMemory({
      content: 'Test memory content ' + Date.now(),
      type: MemoryType.NOTE,
      source: MemorySource.MANUAL,
      importance: 'medium',
    });

    const response = JSON.parse(result.content[0].text);
    expect(response.success).toBe(true);
    expect(response.memory_id).toBeDefined();
    expect(response.type).toBe('note');
  });

  it('should reject duplicate content', async () => {
    const content = 'Unique test content ' + Date.now();

    // Store first time
    await handleStoreMemory({
      content,
      type: MemoryType.NOTE,
      source: MemorySource.MANUAL,
    });

    // Try to store again
    const result = await handleStoreMemory({
      content,
      type: MemoryType.NOTE,
      source: MemorySource.MANUAL,
    });

    const response = JSON.parse(result.content[0].text);
    expect(response.success).toBe(false);
    expect(response.error).toBe('Duplicate memory');
  });

  it('should store memory with context', async () => {
    const result = await handleStoreMemory({
      content: 'function test() { return true; } // ' + Date.now(),
      type: MemoryType.CODE,
      source: MemorySource.IDE,
      context: {
        project: 'test-project',
        file_path: 'src/test.ts',
        language: 'typescript',
        tags: ['function', 'test'],
      },
      importance: 'high',
    });

    const response = JSON.parse(result.content[0].text);
    expect(response.success).toBe(true);
    expect(response.context.project).toBe('test-project');
  });
});
