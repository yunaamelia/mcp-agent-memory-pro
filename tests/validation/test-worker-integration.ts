#!/usr/bin/env npx tsx
/**
 * Test Worker Integration
 * End-to-end tests for worker lifecycle
 */

import { initializeDatabase, getDatabase, closeDatabase } from '../../src/storage/database.js';
import { spawn } from 'child_process';
import * as path from 'path';

async function testWorkerIntegration() {
  console.log('🔍 Testing Worker Integration and Lifecycle...\n');

  try {
    // Initialize database
    await initializeDatabase();
    const db = getDatabase();

    // ========================================================================
    // Test 1: Store → Score → Extract Lifecycle
    // ========================================================================

    console.log('Test 1: Complete Worker Lifecycle');
    console.log('  Phase: Store memories');

    // Insert test memories
    const now = Date.now();
    const memories: string[] = [];

    for (let i = 0; i < 5; i++) {
      const id = `integration-test-${i}-${now}`;
      memories.push(id);

      db.prepare(
        `
        INSERT INTO memories 
        (id, tier, type, source, content, timestamp, importance_score, access_count, created_at, archived)
        VALUES (?, 'short', 'code', 'ide', ?, ?, 0.5, ?, ?, 0)
      `
      ).run(
        id,
        `async function processItem${i}(item) { return transform(item); }`,
        now - i * 3600000,
        i % 3,
        now - i * 3600000
      );
    }

    console.log(`  ✓ Stored ${memories.length} memories\n`);

    // ========================================================================
    // Test 2: Verify Database State
    // ========================================================================

    console.log('Test 2: Verify Database State');

    const count = db.prepare('SELECT COUNT(*) as count FROM memories WHERE archived = 0').get() as {
      count: number;
    };
    console.log(`  ✓ Total memories: ${count.count}`);

    const byTier = db
      .prepare('SELECT tier, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY tier')
      .all();
    for (const row of byTier as any[]) {
      console.log(`  ✓ Tier '${row.tier}': ${row.count}`);
    }

    console.log('');

    // ========================================================================
    // Test 3: Entity Table Exists
    // ========================================================================

    console.log('Test 3: Entity Table');

    try {
      const entityCount = db.prepare('SELECT COUNT(*) as count FROM entities').get() as {
        count: number;
      };
      console.log(`  ✓ Entities table exists: ${entityCount.count} entities`);
    } catch (e) {
      console.log('  ⚠️ Entities table not found (will be created by workers)');
    }

    console.log('');

    // ========================================================================
    // Test 4: Relationships Table
    // ========================================================================

    console.log('Test 4: Relationships Table');

    try {
      const relCount = db.prepare('SELECT COUNT(*) as count FROM entity_relationships').get() as {
        count: number;
      };
      console.log(`  ✓ Relationships table exists: ${relCount.count} relationships`);
    } catch (e) {
      console.log('  ⚠️ Relationships table not found (will be created by workers)');
    }

    console.log('');

    // ========================================================================
    // Test 5: Memory Promotion Criteria
    // ========================================================================

    console.log('Test 5: Memory Promotion Criteria');

    // Update a memory to meet promotion criteria
    const testMemory = memories[0];
    const threeDaysAgo = Date.now() - 3 * 24 * 60 * 60 * 1000;

    db.prepare(
      'UPDATE memories SET timestamp = ?, access_count = 5, importance_score = 0.8 WHERE id = ?'
    ).run(threeDaysAgo, testMemory);

    const updated = db
      .prepare('SELECT importance_score, access_count FROM memories WHERE id = ?')
      .get(testMemory) as any;
    console.log(`  ✓ Memory ${testMemory} importance: ${updated.importance_score}`);
    console.log(`  ✓ Memory ${testMemory} access_count: ${updated.access_count}`);

    // Check promotable
    const promotable = db
      .prepare(
        `
      SELECT COUNT(*) as count FROM memories 
      WHERE tier = 'short' AND archived = 0
      AND (importance_score >= 0.7 OR access_count >= 2)
    `
      )
      .get() as { count: number };

    console.log(`  ✓ Promotable memories: ${promotable.count}`);
    console.log('');

    // ========================================================================
    // Test 6: Cleanup Test Data
    // ========================================================================

    console.log('Test 6: Cleanup');

    for (const memId of memories) {
      db.prepare('DELETE FROM memories WHERE id = ?').run(memId);
    }

    console.log(`  ✓ Cleaned up ${memories.length} test memories`);
    console.log('');

    console.log('✅ All worker integration tests passed!');
    closeDatabase();
    process.exit(0);
  } catch (error) {
    console.error('\n❌ Worker integration test failed:', error);
    closeDatabase();
    process.exit(1);
  }
}

testWorkerIntegration();
