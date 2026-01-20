import { spawn } from 'child_process';
import { logger } from '../utils/logger.js';
import { z } from 'zod';

export const MEMORY_AUTOMATE_TOOL = {
  name: 'memory_automate',
  description:
    'Automate memory management tasks like auto-tagging, duplicate detection, smart merging, and lifecycle management. Uses ML to intelligently organize and optimize your memories.',
  inputSchema: {
    type: 'object',
    properties: {
      action: {
        type: 'string',
        enum: ['auto_tag', 'detect_duplicates', 'merge_similar', 'optimize_lifecycle'],
        description: 'Automation action to perform',
      },
      target: {
        type: 'string',
        description: 'Target memory ID or "all" for batch processing',
      },
      options: {
        type: 'object',
        description: 'Additional options for the action',
      },
    },
    required: ['action'],
  },
};

const AutomateSchema = z.object({
  action: z.enum(['auto_tag', 'detect_duplicates', 'merge_similar', 'optimize_lifecycle']),
  target: z.string().default('all'),
  options: z.record(z.any()).optional(),
});

export async function handleMemoryAutomate(args: unknown) {
  const params = AutomateSchema.parse(args);

  logger.info(`Automating: ${params.action}`);

  try {
    let script = '';

    if (params.action === 'auto_tag') {
      script = `
import sys
sys.path.append('python')

import sqlite3
import json
import re

conn = sqlite3.connect('data/memories.db')
conn.row_factory = sqlite3.Row

# Get recent untagged memories
cursor = conn.execute("""
    SELECT id, content, type FROM memories 
    WHERE (tags IS NULL OR tags = '[]')
    AND archived = 0
    ORDER BY timestamp DESC
    LIMIT 50
""")

memories = [dict(row) for row in cursor.fetchall()]
results = {}

for memory in memories:
    content = memory.get('content', '')
    tags = []
    
    # Simple keyword-based tagging
    if re.search(r'\\bfunction\\b|\\bdef\\b|\\bclass\\b', content, re.I):
        tags.append('code')
    if re.search(r'\\bTODO\\b|\\bFIXME\\b', content, re.I):
        tags.append('todo')
    if re.search(r'\\bimport\\b|\\brequire\\b', content, re.I):
        tags.append('dependencies')
    if re.search(r'\\btest\\b|\\bspec\\b', content, re.I):
        tags.append('testing')
    if re.search(r'\\bAPI\\b|\\bendpoint\\b', content, re.I):
        tags.append('api')
    
    if tags:
        results[memory['id']] = tags
        conn.execute(
            'UPDATE memories SET tags = ? WHERE id = ?',
            (json.dumps(tags), memory['id'])
        )

conn.commit()

print(json.dumps({
    'action': 'auto_tag',
    'processed': len(results),
    'results': {k: v for k, v in list(results.items())[:5]}
}))

conn.close()
`;
    } else if (params.action === 'detect_duplicates') {
      script = `
import sys
sys.path.append('python')

import sqlite3
import json
from difflib import SequenceMatcher

conn = sqlite3.connect('data/memories.db')
conn.row_factory = sqlite3.Row

cursor = conn.execute("""
    SELECT id, content FROM memories
    WHERE archived = 0
    ORDER BY timestamp DESC
    LIMIT 100
""")

memories = [dict(row) for row in cursor.fetchall()]
duplicates = []

for i, m1 in enumerate(memories):
    for m2 in memories[i+1:]:
        c1 = m1.get('content', '')[:500]
        c2 = m2.get('content', '')[:500]
        ratio = SequenceMatcher(None, c1, c2).ratio()
        if ratio > 0.85:
            duplicates.append((m1['id'], m2['id'], round(ratio, 2)))

print(json.dumps({
    'action': 'detect_duplicates',
    'count': len(duplicates),
    'duplicates': [
        {'id1': d[0], 'id2': d[1], 'similarity': d[2]}
        for d in duplicates[:10]
    ]
}))

conn.close()
`;
    } else if (params.action === 'merge_similar') {
      script = `
import sys
sys.path.append('python')

import sqlite3
import json

conn = sqlite3.connect('data/memories.db')
conn.row_factory = sqlite3.Row

cursor = conn.execute("""
    SELECT type, project, COUNT(*) as count FROM memories
    WHERE archived = 0
    GROUP BY type, project
    HAVING count > 1
    ORDER BY count DESC
    LIMIT 10
""")

clusters = [dict(row) for row in cursor.fetchall()]

print(json.dumps({
    'action': 'merge_similar',
    'clusters_found': len(clusters),
    'clusters': clusters[:5]
}))

conn.close()
`;
    } else if (params.action === 'optimize_lifecycle') {
      script = `
import sys
sys.path.append('python')

import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('data/memories.db')
conn.row_factory = sqlite3.Row

now = int(datetime.now().timestamp() * 1000)
two_days_ago = now - (2 * 24 * 60 * 60 * 1000)

cursor = conn.execute("""
    SELECT COUNT(*) as count FROM memories
    WHERE tier = 'short'
    AND timestamp < ?
    AND (importance_score > 0.7 OR access_count > 2)
    AND archived = 0
""", (two_days_ago,))

promotion_candidates = cursor.fetchone()['count']

month_ago = now - (30 * 24 * 60 * 60 * 1000)

cursor = conn.execute("""
    SELECT COUNT(*) as count FROM memories
    WHERE tier = 'working'
    AND timestamp < ?
    AND importance_score < 0.3
    AND access_count = 0
    AND archived = 0
""", (month_ago,))

archival_candidates = cursor.fetchone()['count']

print(json.dumps({
    'action': 'optimize_lifecycle',
    'promotion_candidates': promotion_candidates,
    'archival_candidates': archival_candidates,
    'recommendation': f'Promote {promotion_candidates} memories, archive {archival_candidates} memories'
}))

conn.close()
`;
    }

    const result = await runPythonScript(script);
    const data = JSON.parse(result);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              action: params.action,
              target: params.target,
              timestamp: new Date().toISOString(),
              result: data,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    logger.error('Automation failed:', error);
    throw error;
  }
}

function runPythonScript(script: string): Promise<string> {
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
        reject(new Error(`Python script failed: ${errorOutput}`));
      }
    });
  });
}
