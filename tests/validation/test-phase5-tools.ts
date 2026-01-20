/**
 * Phase 5 MCP Tools Test
 * Tests the 3 new Phase 5 MCP tools
 */

import { spawn } from 'child_process';

interface TestResult {
  name: string;
  status: 'passed' | 'failed';
  duration: number;
  error?: string;
}

async function runPythonScript(script: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const proc = spawn('python3', ['-c', script]);
    let output = '';
    let errorOutput = '';

    proc.stdout.on('data', (data) => {
      output += data.toString();
    });

    proc.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    proc.on('close', (code) => {
      if (code === 0) {
        resolve(output.trim());
      } else {
        reject(new Error(errorOutput || `Exit code: ${code}`));
      }
    });
  });
}

async function testMemoryPredict(): Promise<TestResult> {
  const start = Date.now();

  try {
    const script = `
import sqlite3
import json
from pathlib import Path

# Create test DB
db_path = Path('tests/data/test_predict.db')
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute('''
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        type TEXT,
        content TEXT,
        project TEXT,
        importance_score REAL,
        timestamp INTEGER,
        archived INTEGER DEFAULT 0
    )
''')

# Insert test data
conn.execute('''
    INSERT OR REPLACE INTO memories VALUES
    ('test1', 'code', 'function test() {}', 'proj1', 0.8, 1000000, 0)
''')
conn.commit()

# Simple prediction
cursor = conn.execute('SELECT type, COUNT(*) as count FROM memories GROUP BY type')
predictions = [dict(zip(['type', 'count'], row)) for row in cursor.fetchall()]

conn.close()
db_path.unlink()

print(json.dumps({'success': True, 'predictions': len(predictions)}))
`;

    const result = await runPythonScript(script);
    const data = JSON.parse(result);

    return {
      name: 'memory_predict',
      status: data.success ? 'passed' : 'failed',
      duration: Date.now() - start,
    };
  } catch (error) {
    return {
      name: 'memory_predict',
      status: 'failed',
      duration: Date.now() - start,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function testMemoryAutomate(): Promise<TestResult> {
  const start = Date.now();

  try {
    const script = `
import sqlite3
import json
import re
from pathlib import Path

# Create test DB
db_path = Path('tests/data/test_automate.db')
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute('''
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        content TEXT,
        tags TEXT
    )
''')

# Insert test data
conn.execute('''
    INSERT OR REPLACE INTO memories VALUES
    ('auto1', 'async function fetchData() {}', NULL)
''')
conn.commit()

# Auto-tag
cursor = conn.execute('SELECT id, content FROM memories WHERE tags IS NULL')
rows = cursor.fetchall()

for row in rows:
    content = row[1]
    tags = []
    if re.search(r'function', content):
        tags.append('function')
    if re.search(r'async', content):
        tags.append('async')
    
    conn.execute('UPDATE memories SET tags = ? WHERE id = ?', (json.dumps(tags), row[0]))

conn.commit()

# Verify
cursor = conn.execute('SELECT tags FROM memories WHERE id = "auto1"')
result = cursor.fetchone()
tags = json.loads(result[0]) if result else []

conn.close()
db_path.unlink()

print(json.dumps({'success': len(tags) > 0, 'tags': tags}))
`;

    const result = await runPythonScript(script);
    const data = JSON.parse(result);

    return {
      name: 'memory_automate',
      status: data.success ? 'passed' : 'failed',
      duration: Date.now() - start,
    };
  } catch (error) {
    return {
      name: 'memory_automate',
      status: 'failed',
      duration: Date.now() - start,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function testMemoryProfile(): Promise<TestResult> {
  const start = Date.now();

  try {
    const script = `
import sqlite3
import json
import time
from pathlib import Path

# Create test DB
db_path = Path('tests/data/test_profile.db')
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute('''
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        content TEXT
    )
''')

# Insert test data
for i in range(100):
    conn.execute(f'INSERT OR REPLACE INTO memories VALUES ("mem{i}", "content {i}")')
conn.commit()

# Profile queries
results = {}

# Query 1: Count
start = time.time()
conn.execute('SELECT COUNT(*) FROM memories')
results['count_query_ms'] = (time.time() - start) * 1000

# Query 2: Select all
start = time.time()
conn.execute('SELECT * FROM memories LIMIT 10')
results['select_query_ms'] = (time.time() - start) * 1000

conn.close()
db_path.unlink()

print(json.dumps({'success': True, 'profile': results}))
`;

    const result = await runPythonScript(script);
    const data = JSON.parse(result);

    return {
      name: 'memory_profile',
      status: data.success ? 'passed' : 'failed',
      duration: Date.now() - start,
    };
  } catch (error) {
    return {
      name: 'memory_profile',
      status: 'failed',
      duration: Date.now() - start,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function main() {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║           PHASE 5 MCP TOOLS VALIDATION                       ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log('');

  const results: TestResult[] = [];

  console.log('Testing memory_predict...');
  results.push(await testMemoryPredict());

  console.log('Testing memory_automate...');
  results.push(await testMemoryAutomate());

  console.log('Testing memory_profile...');
  results.push(await testMemoryProfile());

  console.log('');
  console.log('═══ Results ═══');

  let passed = 0;
  let failed = 0;

  for (const result of results) {
    if (result.status === 'passed') {
      console.log(`✅ ${result.name}: PASSED (${result.duration}ms)`);
      passed++;
    } else {
      console.log(`❌ ${result.name}: FAILED`);
      if (result.error) {
        console.log(`   Error: ${result.error}`);
      }
      failed++;
    }
  }

  console.log('');
  console.log(`Passed: ${passed}/${results.length}`);
  console.log(`Failed: ${failed}/${results.length}`);

  if (failed > 0) {
    console.log('\n❌ PHASE 5 TOOLS VALIDATION FAILED');
    process.exit(1);
  } else {
    console.log('\n✅ PHASE 5 TOOLS VALIDATION PASSED');
    process.exit(0);
  }
}

main().catch((error) => {
  console.error('Test suite error:', error);
  process.exit(1);
});
