#!/usr/bin/env node

import { initializeDatabase, getDatabase, closeDatabase } from '../../src/storage/database.js';
import { randomUUID } from 'crypto';

async function validateDatabase() {
  console.log('🔍 Validating Database Operations...\n');

  try {
    // Initialize
    await initializeDatabase();
    const db = getDatabase();

    // Test 1: Basic INSERT
    console.log('Test 1: Basic INSERT');
    const testId = randomUUID();
    const timestamp = Date.now();

    db.prepare(
      `
      INSERT INTO memories (
        id, tier, type, source, content, content_hash,
        timestamp, importance_score, created_at, last_accessed
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `
    ).run(
      testId,
      'short',
      'note',
      'manual',
      'Test content for validation',
      'test-hash-' + testId,
      timestamp,
      0.5,
      timestamp,
      timestamp
    );

    console.log('  ✓ INSERT successful');

    // Test 2: SELECT
    console.log('\nTest 2: SELECT');
    const row = db.prepare('SELECT * FROM memories WHERE id = ?').get(testId);

    if (!row) {
      throw new Error('Failed to retrieve inserted row');
    }

    console.log('  ✓ SELECT successful');

    // Test 3: UPDATE
    console.log('\nTest 3: UPDATE');
    db.prepare('UPDATE memories SET access_count = access_count + 1 WHERE id = ?').run(testId);

    const updated = db.prepare('SELECT access_count FROM memories WHERE id = ?').get(testId) as {
      access_count: number;
    };

    if (updated.access_count !== 1) {
      throw new Error('UPDATE failed');
    }

    console.log('  ✓ UPDATE successful');

    // Test 4: FTS5 Search
    console.log('\nTest 4: FTS5 Full-Text Search');
    const ftsResults = db
      .prepare('SELECT * FROM memories_fts WHERE memories_fts MATCH ?')
      .all('validation');

    if (ftsResults.length === 0) {
      throw new Error('FTS5 search returned no results');
    }

    console.log(`  ✓ FTS5 search successful (${ftsResults.length} results)`);

    // Test 5: Indexes
    console.log('\nTest 5: Index Performance');
    const indexedQuery = db
      .prepare('SELECT * FROM memories WHERE type = ? AND archived = 0')
      .all('note');

    console.log(`  ✓ Indexed query successful (${indexedQuery.length} results)`);

    // Test 6: Foreign Key Constraints
    console.log('\nTest 6: Foreign Key Constraints');
    try {
      db.prepare(
        'INSERT INTO memories (id, tier, type, source, content, content_hash, timestamp, created_at, promoted_from) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
      ).run(
        randomUUID(),
        'working',
        'note',
        'manual',
        'Test',
        'hash',
        Date.now(),
        Date.now(),
        'non-existent-id'
      );
      throw new Error('Foreign key constraint not enforced');
    } catch (error) {
      if ((error as Error).message.includes('FOREIGN KEY')) {
        console.log('  ✓ Foreign key constraints working');
      } else {
        throw error;
      }
    }

    // Test 7: Statistics Table
    console.log('\nTest 7: Statistics Table');
    const stats = db.prepare("SELECT * FROM statistics WHERE key = 'total_memories'").get();

    if (!stats) {
      throw new Error('Statistics table not initialized');
    }

    console.log('  ✓ Statistics table working');

    // Test 8: Configuration Table
    console.log('\nTest 8: Configuration Table');
    const config = db.prepare("SELECT * FROM config WHERE key = 'version'").get();

    if (!config) {
      throw new Error('Configuration table not initialized');
    }

    console.log('  ✓ Configuration table working');

    // Cleanup
    db.prepare('DELETE FROM memories WHERE id = ?').run(testId);

    console.log('\n✅ All database tests passed!');
    closeDatabase();
    process.exit(0);
  } catch (error) {
    console.error('\n❌ Database validation failed:', error);
    closeDatabase();
    process.exit(1);
  }
}

validateDatabase();
