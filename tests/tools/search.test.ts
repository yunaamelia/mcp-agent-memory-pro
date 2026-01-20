import { jest, describe, it, expect, beforeAll, afterAll } from '@jest/globals';
import { handleSearchMemory } from '../../src/tools/search.js';
import { handleStoreMemory } from '../../src/tools/store.js';
import { initializeDatabase, closeDatabase } from '../../src/storage/database.js';
import { initializeVectorStore } from '../../src/storage/vector-store.js';
import { MemoryType, MemorySource } from '../../src/types/memory.js';

import { embeddingClient } from '../../src/services/embedding-client.js';

jest.spyOn(embeddingClient, 'generateEmbedding').mockResolvedValue(new Array(384).fill(0.1));

describe('Search Memory Tool', () => {
  beforeAll(async () => {
    await initializeDatabase();
    await initializeVectorStore();

    // Store test memories
    await handleStoreMemory({
      content: 'JavaScript programming tutorial',
      type: MemoryType.NOTE,
      source: MemorySource.MANUAL,
    });

    await handleStoreMemory({
      content: 'Python machine learning guide',
      type: MemoryType.NOTE,
      source: MemorySource.MANUAL,
    });
  });

  afterAll(() => {
    closeDatabase();
  });

  it('should search and return results', async () => {
    const result = await handleSearchMemory({
      query: 'programming',
      limit: 10,
    });

    const response = JSON.parse(result.content[0].text);
    expect(response.count).toBeGreaterThan(0);
    expect(response.results).toBeDefined();
  });

  it('should filter by type', async () => {
    const result = await handleSearchMemory({
      query: 'tutorial',
      filters: {
        types: [MemoryType.NOTE],
      },
      limit: 10,
    });

    const response = JSON.parse(result.content[0].text);
    response.results.forEach((r: any) => {
      expect(r.type).toBe('note');
    });
  });

  it('should respect limit parameter', async () => {
    const result = await handleSearchMemory({
      query: 'guide',
      limit: 1,
    });

    const response = JSON.parse(result.content[0].text);
    expect(response.results.length).toBeLessThanOrEqual(1);
  });
});
