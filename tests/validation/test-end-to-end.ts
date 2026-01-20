#!/usr/bin/env node

import { handleStoreMemory } from '../../src/tools/store.js';
import { handleSearchMemory } from '../../src/tools/search.js';
import { initializeDatabase, closeDatabase } from '../../src/storage/database.js';
import { initializeVectorStore } from '../../src/storage/vector-store.js';
import { embeddingClient } from '../../src/services/embedding-client.js';
import { MemoryType, MemorySource } from '../../src/types/memory.js';

async function validateEndToEnd() {
  console.log('🔍 Validating End-to-End Workflow...\n');

  try {
    // Setup
    await initializeDatabase();
    await initializeVectorStore();
    await embeddingClient.waitForService();

    // Scenario: User learns a new coding concept and then recalls it later
    const concept = 'The Adapter Pattern allows incompatible interfaces to work together.';
    const context = {
      project: 'design-patterns',
      language: 'typescript',
      tags: ['patterns', 'structural'],
    };

    // Step 1: Store the memory
    console.log('Step 1: Storing memory...');
    const storeResult = await handleStoreMemory({
      content: concept,
      type: MemoryType.NOTE,
      source: MemorySource.MANUAL,
      context,
      importance: 'high',
    });

    const storeResponse = JSON.parse(storeResult.content[0].text);
    if (!storeResponse.success) throw new Error('Failed to store memory');
    console.log('  ✓ Memory stored');

    // Step 2: Search for the memory by semantic meaning (not exact match)
    console.log('\nStep 2: Searching by meaning...');
    const query = 'How to make incompatible classes compatible?';

    const searchResult = await handleSearchMemory({
      query,
      limit: 1,
      filters: {
        projects: ['design-patterns'],
      },
    });

    const searchResponse = JSON.parse(searchResult.content[0].text);
    if (!searchResponse.results || searchResponse.results.length === 0) {
      throw new Error('No results found for semantic query');
    }

    const topResult = searchResponse.results[0];
    console.log(`  ✓ Top result: "${topResult.content}"`);
    console.log(`  ✓ Similarity: ${topResult.similarity_score}`);

    if (topResult.content !== concept) {
      throw new Error('Retrieved memory does not match stored memory');
    }

    if (topResult.project !== context.project) {
      throw new Error('Metadata (project) not preserved');
    }

    console.log('  ✓ Semantic retrieval successful');

    console.log('\n✅ End-to-End validation passed!');
    closeDatabase();
    process.exit(0);
  } catch (error) {
    console.error('\n❌ End-to-End validation failed:', error);
    closeDatabase();
    process.exit(1);
  }
}

validateEndToEnd();
