#!/usr/bin/env node

import { handleStoreMemory } from '../../src/tools/store.js';
import { handleSearchMemory } from '../../src/tools/search.js';
import { initializeDatabase, closeDatabase } from '../../src/storage/database.js';
import { initializeVectorStore } from '../../src/storage/vector-store.js';
import { embeddingClient } from '../../src/services/embedding-client.js';
import { MemoryType, MemorySource } from '../../src/types/memory.js';

async function validateMCPTools() {
  console.log('🔍 Validating MCP Tools...\n');

  try {
    // Setup
    await initializeDatabase();
    await initializeVectorStore();

    // Ensure embedding service is ready
    await embeddingClient.waitForService();

    // Test 1: Store Memory Tool
    console.log('Test 1: Store Memory Tool');
    const storeParams = {
      content: 'MCP Tool Validation Test',
      type: MemoryType.NOTE,
      source: MemorySource.MANUAL,
      importance: 'high',
    };

    const storeResult = await handleStoreMemory(storeParams);
    const storeResponse = JSON.parse(storeResult.content[0].text);

    if (!storeResponse.success) {
      throw new Error(`Store tool failed: ${storeResponse.error}`);
    }

    if (!storeResponse.memory_id) {
      throw new Error('Store tool did not return memory_id');
    }

    console.log(`  ✓ Store tool successful (ID: ${storeResponse.memory_id})`);

    // Test 2: Search Memory Tool
    console.log('\nTest 2: Search Memory Tool');
    const searchParams = {
      query: 'Validation Test',
      limit: 5,
    };

    const searchResult = await handleSearchMemory(searchParams);
    const searchResponse = JSON.parse(searchResult.content[0].text);

    if (searchResponse.count === 0) {
      throw new Error('Search tool returned no results');
    }

    const found = searchResponse.results.find((m: any) => m.content === storeParams.content);
    if (!found) {
      throw new Error('Search tool did not find stored memory');
    }

    console.log(`  ✓ Search tool successful (Found ${searchResponse.count} results)`);

    // Cleanup happens via database close
    console.log('\n✅ All MCP tool tests passed!');
    closeDatabase();
    process.exit(0);
  } catch (error) {
    console.error('\n❌ MCP tools validation failed:', error);
    closeDatabase();
    process.exit(1);
  }
}

validateMCPTools();
