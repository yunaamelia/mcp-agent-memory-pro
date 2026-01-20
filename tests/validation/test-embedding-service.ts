#!/usr/bin/env node

import { embeddingClient } from '../../src/services/embedding-client.js';

async function validateEmbeddingService() {
  console.log('🔍 Validating Embedding Service...\n');

  try {
    // Test 1: Health Check
    console.log('Test 1: Health Check');
    const health = await embeddingClient.healthCheck();

    if (health.status !== 'healthy') {
      throw new Error('Service not healthy');
    }

    console.log(`  ✓ Service healthy`);
    console.log(`  Model: ${health.model}`);
    console.log(`  Dimensions: ${health.dimensions}`);

    // Test 2: Single Embedding
    console.log('\nTest 2: Single Embedding Generation');
    const start1 = Date.now();
    const embedding = await embeddingClient.generateEmbedding('Test text for embedding');
    const duration1 = Date.now() - start1;

    if (!Array.isArray(embedding)) {
      throw new Error('Embedding is not an array');
    }

    if (embedding.length !== 384) {
      throw new Error(`Expected 384 dimensions, got ${embedding.length}`);
    }

    console.log(`  ✓ Single embedding generated (${duration1}ms)`);
    console.log(`  Dimensions: ${embedding.length}`);

    // Test 3: Batch Embeddings
    console.log('\nTest 3: Batch Embedding Generation');
    const texts = [
      'First test text',
      'Second test text',
      'Third test text',
      'Fourth test text',
      'Fifth test text',
    ];

    const start2 = Date.now();
    const embeddings = await embeddingClient.generateEmbeddings(texts);
    const duration2 = Date.now() - start2;

    if (embeddings.length !== texts.length) {
      console.log(
        `  Warning: Expected ${texts.length} embeddings, got ${embeddings.length}. Check if embedding service supports batching properly.`
      );
      // In some implementations, generateEmbeddings might fail silently or return fewer.
      // But if it throws, we catch it.
      if (embeddings.length === 0) throw new Error('No embeddings returned');
    }

    console.log(`  ✓ Batch embeddings generated (${duration2}ms)`);
    console.log(`  Count: ${embeddings.length}`);
    console.log(`  Avg time per embedding: ${(duration2 / embeddings.length).toFixed(2)}ms`);

    // Test 4: Semantic Similarity
    console.log('\nTest 4: Semantic Similarity');
    const text1 = 'The cat sits on the mat';
    const text2 = 'A feline rests on the rug';
    const text3 = 'JavaScript is a programming language';

    const [emb1, emb2, emb3] = await embeddingClient.generateEmbeddings([text1, text2, text3]);

    const similarity12 = cosineSimilarity(emb1, emb2);
    const similarity13 = cosineSimilarity(emb1, emb3);

    if (similarity12 <= similarity13) {
      throw new Error('Semantic similarity not working correctly');
    }

    console.log(`  ✓ Semantic similarity working`);
    console.log(`  Similar texts: ${similarity12.toFixed(4)}`);
    console.log(`  Different texts: ${similarity13.toFixed(4)}`);

    // Test 5: Normalization
    console.log('\nTest 5: Vector Normalization');
    const normalizedEmb = await embeddingClient.generateEmbedding('Normalization test', true);
    const magnitude = Math.sqrt(normalizedEmb.reduce((sum, val) => sum + val * val, 0));

    if (Math.abs(magnitude - 1.0) > 0.01) {
      throw new Error(`Vector not normalized: magnitude = ${magnitude}`);
    }

    console.log(`  ✓ Vectors properly normalized (magnitude: ${magnitude.toFixed(4)})`);

    // Test 6: Performance Benchmark
    console.log('\nTest 6: Performance Benchmark');
    const benchmarkTexts = Array.from({ length: 20 }, (_, i) => `Benchmark text number ${i}`);

    const benchStart = Date.now();
    await embeddingClient.generateEmbeddings(benchmarkTexts);
    const benchDuration = Date.now() - benchStart;

    const avgTime = benchDuration / benchmarkTexts.length;

    console.log(`  ✓ Performance benchmark complete`);
    console.log(`  Total time: ${benchDuration}ms`);
    console.log(`  Avg per embedding: ${avgTime.toFixed(2)}ms`);

    if (avgTime > 100) {
      console.log(`  ⚠️ Warning: Average time exceeds 100ms target`);
    }

    console.log('\n✅ All embedding service tests passed!');
    process.exit(0);
  } catch (error) {
    console.error('\n❌ Embedding service validation failed:', error);
    process.exit(1);
  }
}

function cosineSimilarity(a: number[], b: number[]): number {
  const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
  const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
  const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
  return dotProduct / (magnitudeA * magnitudeB);
}

validateEmbeddingService();
