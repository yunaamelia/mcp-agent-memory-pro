#!/usr/bin/env node

import { handleStoreMemory } from '../../src/tools/store.js';
import { handleSearchMemory } from '../../src/tools/search.js';
import { initializeDatabase, closeDatabase } from '../../src/storage/database.js';
import { initializeVectorStore } from '../../src/storage/vector-store.js';
import { embeddingClient } from '../../src/services/embedding-client.js';
import { MemoryType, MemorySource } from '../../src/types/memory.js';

async function validatePerformance() {
  console.log('🔍 Running Performance Benchmarks...\n');

  try {
    // Setup
    await initializeDatabase();
    await initializeVectorStore();
    await embeddingClient.waitForService();

    // Configuration
    const BATCH_SIZE = 20;
    const TARGET_STORE_MS = 200; // Average target per memory
    const TARGET_SEARCH_MS = 100;

    // Benchmark 1: Bulk Storage
    console.log(`Benchmark 1: Storing ${BATCH_SIZE} memories...`);

    const startStore = Date.now();
    for (let i = 0; i < BATCH_SIZE; i++) {
      await handleStoreMemory({
        content: `Performance test memory content #${i} - ${Math.random()}`,
        type: MemoryType.NOTE,
        source: MemorySource.MANUAL,
        importance: 'low',
      });
    }
    const endStore = Date.now();
    const totalStoreTime = endStore - startStore;
    const avgStoreTime = totalStoreTime / BATCH_SIZE;

    console.log(`  Total time: ${totalStoreTime}ms`);
    console.log(`  Avg per item: ${avgStoreTime.toFixed(2)}ms`);

    if (avgStoreTime > TARGET_STORE_MS) {
      console.warn(`  ⚠️  Store performance below target (${TARGET_STORE_MS}ms)`);
    } else {
      console.log(`  ✓ Store performance within target`);
    }

    // Benchmark 2: Search Latency
    console.log(`\nBenchmark 2: Search Latency (${BATCH_SIZE} queries)...`);

    const startSearch = Date.now();
    for (let i = 0; i < BATCH_SIZE; i++) {
      await handleSearchMemory({
        query: `Performance test query #${i}`,
        limit: 5,
      });
    }
    const endSearch = Date.now();
    const totalSearchTime = endSearch - startSearch;
    const avgSearchTime = totalSearchTime / BATCH_SIZE;

    console.log(`  Total time: ${totalSearchTime}ms`);
    console.log(`  Avg per query: ${avgSearchTime.toFixed(2)}ms`);

    if (avgSearchTime > TARGET_SEARCH_MS) {
      console.warn(`  ⚠️  Search performance below target (${TARGET_SEARCH_MS}ms)`);
    } else {
      console.log(`  ✓ Search performance within target`);
    }

    console.log('\n✅ Performance benchmarks completed!');
    closeDatabase();
    process.exit(0);
  } catch (error) {
    console.error('\n❌ Performance benchmarks failed:', error);
    closeDatabase();
    process.exit(1);
  }
}

validatePerformance();
