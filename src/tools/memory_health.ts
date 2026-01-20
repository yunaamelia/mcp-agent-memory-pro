import { spawn } from 'child_process';
import { logger } from '../utils/logger.js';

export const MEMORY_HEALTH_TOOL = {
  name: 'memory_health',
  description:
    'Get comprehensive system health status including database health, storage usage, memory tier distribution, and worker status.  Provides health score and recommendations.',
  inputSchema: {
    type: 'object',
    properties: {
      detailed: {
        type: 'boolean',
        description: 'Include detailed metrics (default: false)',
      },
    },
  },
};

export async function handleMemoryHealth(args: unknown) {
  const params = (args as any) || {};
  const detailed = params.detailed || false;

  logger.info('Checking system health');

  try {
    const script = `
import sys
sys.path.append('python')

from monitoring.health_monitor import HealthMonitor
import sqlite3
import json
from pathlib import Path
import os

db_path = os.getenv('MCP_MEMORY_DB_PATH', 'data/memories.db')
data_dir = os.getenv('MCP_MEMORY_DATA_DIR', 'data')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

monitor = HealthMonitor(conn, Path(data_dir))
health = monitor.get_health_status()

print(json.dumps(health, default=str))
conn.close()
`;

    const result = await runPythonScript(script);
    const health = JSON.parse(result);

    const summary: any = {
      overall_status: health.overall_status,
      database_status: health.database.status,
      storage_percent: health.storage.percent_used,
      health_score: health.database.status === 'healthy' ? 100 : 75,
      timestamp: health.timestamp,
    };

    if (detailed) {
      summary.details = health;
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(summary, null, 2),
        },
      ],
    };
  } catch (error) {
    logger.error('Health check failed:', error);
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
