import { jest, describe, it, expect, beforeAll, afterAll } from '@jest/globals';
import { handleStoreMemory, handleSearchMemory } from '../../src/tools/index.js';
import { dbManager } from '../../src/storage/database.js';
// import { vectorStore } from '../../src/storage/vector-store.js';
import { embeddingClient } from '../../src/services/embedding-client.js';

// Mock embedding client to avoid needing Python service running
// jest.mock('../../src/services/embedding-client.js');

describe('Memory Integration Flow', () => {
  beforeAll(async () => {
    // Ensure clean state (using in-memory or temp file would be better, but we are using default config for now)
    // For safety in tests, we might want to config to use :memory: or temp paths if possible.
    // However, config is a singleton loaded from env.
    // We can mock the config values if we refactor config to be injectable or mutable for tests.
    // For Phase 1 simple verification, let's assume we are running in a test env or acceptable to use the dev db.
    // BETTER: Mock the dependencies completely or use a separate test config.

    // For now, let's mock the embedding response
    jest.spyOn(embeddingClient, 'generateEmbedding').mockResolvedValue(new Array(384).fill(0.1));
  });

  afterAll(() => {
    dbManager.close();
    jest.restoreAllMocks();
  });

  it('should store and retrieve a memory', async () => {
    const content = `The project "Apollo" uses React and TypeScript. ${Date.now()}`;

    // 1. Store
    const storeResult = await handleStoreMemory({
      content,
      type: 'note',
      tier: 'short',
      source: 'manual',
      context: {
        project: 'Apollo',
        tags: ['react', 'typescript'],
      },
    });

    const storeResponse = JSON.parse(storeResult.content[0].text);
    expect(storeResponse.success).toBe(true);
    expect(storeResponse.memory_id).toBeDefined();

    // 2. Search
    const searchResult = await handleSearchMemory({
      query: 'What does Apollo use?',
      limit: 1,
    });

    const searchResponse = JSON.parse(searchResult.content[0].text);
    expect(searchResponse.results).toBeDefined();
    expect(Array.isArray(searchResponse.results)).toBe(true);
    expect(searchResponse.results.length).toBeGreaterThan(0);

    const memory = searchResponse.results[0];
    expect(memory.content).toBe(content);
    expect(memory.project).toBe('Apollo');
  });
});
