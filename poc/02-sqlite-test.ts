/**
 * Proof of Concept: SQLite with FTS5 full-text search
 * Validates: better-sqlite3 works, FTS5 enabled
 */

import Database from 'better-sqlite3';
import { mkdirSync, rmSync } from 'fs';
import { join } from 'path';

const TEST_DIR = join(process.cwd(), 'poc/data');
const DB_PATH = join(TEST_DIR, 'test.db');

// Clean start
rmSync(DB_PATH, { force: true });
mkdirSync(TEST_DIR, { recursive: true });

const db = new Database(DB_PATH);

// Test 1: Basic CRUD
console.log('✓ Testing basic CRUD...');
db.exec(`
  CREATE TABLE IF NOT EXISTS test_table (
    id INTEGER PRIMARY KEY,
    content TEXT
  )
`);

const insert = db.prepare('INSERT INTO test_table (content) VALUES (?)');
insert.run('Hello World');

const select = db.prepare('SELECT * FROM test_table');
const rows = select.all();
console.log('  Inserted and retrieved:', rows);

// Test 2: FTS5 availability
console.log('✓ Testing FTS5...');
try {
    db.exec(`
    CREATE VIRTUAL TABLE IF NOT EXISTS test_fts USING fts5(content);
    INSERT INTO test_fts(content) VALUES ('TypeScript is great');
    INSERT INTO test_fts(content) VALUES ('JavaScript is flexible');
    INSERT INTO test_fts(content) VALUES ('Python for machine learning');
  `);

    const ftsSearch = db.prepare('SELECT * FROM test_fts WHERE test_fts MATCH ?');
    const ftsResults = ftsSearch.all('TypeScript');
    console.log('  FTS5 search results:', ftsResults);

    if (ftsResults.length > 0) {
        console.log('  ✅ FTS5 is working!');
    }
} catch (error) {
    console.error('❌ FTS5 not available:', error);
    process.exit(1);
}

// Test 3: JSON support
console.log('✓ Testing JSON support...');
db.exec(`
  CREATE TABLE IF NOT EXISTS test_json (
    id INTEGER PRIMARY KEY,
    data TEXT
  )
`);

const jsonInsert = db.prepare('INSERT INTO test_json (data) VALUES (?)');
jsonInsert.run(JSON.stringify({ tags: ['ai', 'mcp', 'memory'] }));

const jsonSelect = db.prepare('SELECT data FROM test_json WHERE id = 1');
const jsonRow = jsonSelect.get() as { data: string };
const parsed = JSON.parse(jsonRow.data);
console.log('  JSON roundtrip:', parsed);

db.close();
console.log('\n✅ All SQLite tests passed!');
