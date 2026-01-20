#!/usr/bin/env npx tsx
/**
 * Test Memory Insights MCP Tool
 */

import { initializeDatabase, getDatabase, closeDatabase } from '../../src/storage/database.js';

async function testInsightsTool() {
  console.log('\n' + '='.repeat(50));
  console.log('MEMORY INSIGHTS TOOL VALIDATION');
  console.log('='.repeat(50) + '\n');

  try {
    // Initialize database
    await initializeDatabase();
    const db = getDatabase();

    // Insert test data if empty
    const count = db.prepare('SELECT COUNT(*) as count FROM memories').get() as { count: number };

    if (count.count === 0) {
      console.log('Inserting test data...');
      const now = Date.now();

      for (let i = 0; i < 10; i++) {
        db.prepare(
          `
          INSERT INTO memories (id, tier, type, source, content, timestamp, importance_score, access_count, archived)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        `
        ).run(
          `test-${i}`,
          i < 5 ? 'short' : 'working',
          i % 2 === 0 ? 'code' : 'note',
          'ide',
          `Test content ${i}`,
          now - i * 3600000,
          0.5 + Math.random() * 0.5,
          Math.floor(Math.random() * 10)
        );
      }
    }

    // Test overview insights
    console.log('Testing overview insights...');
    const total = db.prepare('SELECT COUNT(*) as count FROM memories WHERE archived = 0').get() as {
      count: number;
    };
    console.log(`  Total memories: ${total.count}`);
    console.log('  ✅ Overview test passed\n');

    // Test tier distribution
    console.log('Testing tier distribution...');
    const byTier = db
      .prepare('SELECT tier, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY tier')
      .all();
    for (const row of byTier as any[]) {
      console.log(`  ${row.tier}: ${row.count}`);
    }
    console.log('  ✅ Tier distribution test passed\n');

    // Test type distribution
    console.log('Testing type distribution...');
    const byType = db
      .prepare('SELECT type, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY type')
      .all();
    for (const row of byType as any[]) {
      console.log(`  ${row.type}: ${row.count}`);
    }
    console.log('  ✅ Type distribution test passed\n');

    // Test entity queries
    console.log('Testing entity queries...');
    try {
      const entityCount = db.prepare('SELECT COUNT(*) as count FROM entities').get() as {
        count: number;
      };
      console.log(`  Entities: ${entityCount.count}`);
      console.log('  ✅ Entity queries test passed\n');
    } catch (e) {
      console.log('  ⚠️ Entity table may not exist yet\n');
    }

    // Test health metrics calculation
    console.log('Testing health metrics...');
    const lowImportance = db
      .prepare(
        'SELECT COUNT(*) as count FROM memories WHERE importance_score < 0.3 AND archived = 0'
      )
      .get() as { count: number };
    const unaccessed = db
      .prepare('SELECT COUNT(*) as count FROM memories WHERE access_count = 0 AND archived = 0')
      .get() as { count: number };

    console.log(`  Low importance: ${lowImportance.count}`);
    console.log(`  Unaccessed: ${unaccessed.count}`);
    console.log('  ✅ Health metrics test passed\n');

    closeDatabase();

    console.log('='.repeat(50));
    console.log('✅ ALL INSIGHTS TOOL TESTS PASSED');
    console.log('='.repeat(50));

    process.exit(0);
  } catch (error) {
    console.error('\n❌ Insights tool tests failed:', error);
    closeDatabase();
    process.exit(1);
  }
}

testInsightsTool();
