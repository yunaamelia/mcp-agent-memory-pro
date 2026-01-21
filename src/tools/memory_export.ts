import { spawn } from 'child_process';
import { logger } from '../utils/logger.js';
import { z } from 'zod';

export const MEMORY_EXPORT_TOOL = {
  name: 'memory_export',
  description:
    'Export memories to JSON or CSV format.  Supports filtering by project, type, and tier. Can create full backups with all data including entities and relationships.',
  inputSchema: {
    type: 'object',
    properties: {
      format: {
        type: 'string',
        enum: ['json', 'csv', 'backup'],
        description: 'Export format (json, csv, or backup for full backup)',
      },
      output_path: {
        type: 'string',
        description: 'Output file path (optional, auto-generated if not provided)',
      },
      filters: {
        type: 'object',
        properties: {
          project: { type: 'string' },
          type: { type: 'string' },
          tier: { type: 'string' },
        },
        description: 'Optional filters for export',
      },
    },
    required: ['format'],
  },
};

const ExportSchema = z.object({
  format: z.enum(['json', 'csv', 'backup']),
  output_path: z.string().optional(),
  filters: z
    .object({
      project: z.string().optional(),
      type: z.string().optional(),
      tier: z.string().optional(),
    })
    .optional(),
});

export async function handleMemoryExport(args: unknown) {
  const params = ExportSchema.parse(args);

  logger.info(`Exporting memories to ${params.format}`);

  try {
    const outputPath =
      params.output_path ||
      `data/exports/export_${Date.now()}.${params.format === 'backup' ? 'zip' : params.format}`;

    const script = `
import sys
sys.path.append('python')

from data_management.export_service import ExportService
import sqlite3
import json
import os

db_path = os.getenv('MCP_MEMORY_DB_PATH', 'data/memories.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

service = ExportService(conn)

filters_json = '''${JSON.stringify(params.filters || null)}'''
filters = json.loads(filters_json)

if '${params.format}' == 'json':
    result = service.export_to_json('${outputPath}', filters)
elif '${params.format}' == 'csv':
    result = service.export_to_csv('${outputPath}', filters)
elif '${params.format}' == 'backup':
    result = service.export_full_backup('${outputPath}')

print(json.dumps(result))
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
              success: data.success,
              format: params.format,
              output_path: data.output_path,
              count: data.count ?? data.memory_count,
              size_mb: (data.size_bytes / (1024 * 1024)).toFixed(2),
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    logger.error('Export failed:', error);
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
