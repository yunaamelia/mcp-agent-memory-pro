#!/usr/bin/env node

import { initializeVectorStore, addVector, searchVectors } from '../../src/storage/vector-store.js';
import { randomUUID } from 'crypto';

async function validateVectorStore() {
  console.log('🔍 Validating Vector Store Operations...\n');

  try {
    // Initialize
    await initializeVectorStore();

    // Test 1: Add Vector
    console.log('Test 1: Add Vector');
    const testId = randomUUID();
    const testVector = new Array(384).fill(0).map(() => Math.random());

    await addVector(testId, testVector, {
      content: 'Test vector content',
      timestamp: Date.now(),
      type: 'note',
      tier: 'short',
    });

    console.log('  ✓ Vector added successfully');

    // Test 2: Search Vectors
    console.log('\nTest 2: Search Vectors');
    const queryVector = new Array(384).fill(0).map(() => Math.random());
    const results = await searchVectors(queryVector, 5);

    if (results.length === 0) {
      throw new Error('Vector search returned no results');
    }

    console.log(`  ✓ Vector search successful (${results.length} results)`);

    // Test 3: Similarity Ordering
    console.log('\nTest 3: Similarity Ordering');
    const distances = results.map((r) => r._distance);

    for (let i = 1; i < distances.length; i++) {
      if (distances[i] < distances[i - 1]) {
        throw new Error('Results not ordered by distance');
      }
    }

    console.log('  ✓ Results properly ordered by similarity');

    // Test 4: Filtered Search
    console.log('\nTest 4: Filtered Search');
    const filteredResults = await searchVectors(queryVector, 5, "type = 'note'");

    for (const result of filteredResults) {
      if (result.type !== 'note') {
        throw new Error('Filter not applied correctly');
      }
    }

    console.log(`  ✓ Filtered search successful (${filteredResults.length} results)`);

    // Test 5: High-Dimensional Vectors
    console.log('\nTest 5: High-Dimensional Vector Handling');
    const highDimId = randomUUID();
    const highDimVector = new Array(384).fill(0).map((_, i) => Math.sin(i / 10));

    await addVector(highDimId, highDimVector, {
      content: 'High-dimensional test',
      timestamp: Date.now(),
      type: 'note',
      tier: 'short',
    });

    console.log('  ✓ High-dimensional vectors handled correctly');

    // Test 6: Batch Operations
    console.log('\nTest 6: Batch Operations');
    const batchIds = Array.from({ length: 10 }, () => randomUUID());

    for (const id of batchIds) {
      await addVector(
        id,
        new Array(384).fill(0).map(() => Math.random()),
        {
          content: `Batch test ${id}`,
          timestamp: Date.now(),
          type: 'note',
          tier: 'short',
        }
      );
    }

    console.log('  ✓ Batch operations successful');

    console.log('\n✅ All vector store tests passed!');
    process.exit(0);
  } catch (error) {
    console.error('\n❌ Vector store validation failed:', error);
    process.exit(1);
  }
}

validateVectorStore();
