import { spawn } from 'child_process';
import { logger } from '../utils/logger.js';
import { z } from 'zod';

export const MEMORY_QUERY_TOOL = {
  name: 'memory_query',
  description:
    'Query memories using MemQL - a SQL-like query language.  Supports SELECT, WHERE, ORDER BY, and LIMIT.  Examples: "SELECT * FROM memories WHERE type = \'code\' LIMIT 10" or "SELECT content, importance_score FROM memories WHERE importance_score > 0.8 ORDER BY timestamp DESC"',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'MemQL query string (SQL-like syntax)',
      },
    },
    required: ['query'],
  },
};

const QuerySchema = z.object({
  query: z.string().min(1),
});

export async function handleMemoryQuery(args: unknown) {
  const params = QuerySchema.parse(args);

  logger.info(`Executing MemQL query: ${params.query}`);

  try {
    const script = `
import sys
sys.path.append('python')

from query.memql_executor import MemQLExecutor
import sqlite3
import json
import os

db_path = os.getenv('MCP_MEMORY_DB_PATH', 'data/memories.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

executor = MemQLExecutor(conn)
result = executor.execute("""${params.query}""")

print(json.dumps(result, default=str))
conn.close()
`;

    const result = await runPythonScript(script);
    const data = JSON.parse(result);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              query: params.query,
              count: data.count,
              results: data.results,
              sql: data.sql,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    logger.error('MemQL query failed:', error);
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
        reject(new Error(`Python script failed:  ${errorOutput}`));
      }
    });
  });
}
