import { spawn } from 'child_process';
import { logger } from '../utils/logger.js';
import { z } from 'zod';

export const MEMORY_DASHBOARD_TOOL = {
  name: 'memory_dashboard',
  description:
    'Get comprehensive analytics dashboard with overview statistics, activity timeline, top entities, project breakdown, and usage stats.  Perfect for understanding memory system usage and trends.',
  inputSchema: {
    type: 'object',
    properties: {
      sections: {
        type: 'array',
        items: {
          type: 'string',
          enum: ['overview', 'timeline', 'entities', 'projects', 'usage'],
        },
        description: 'Dashboard sections to include (default: all)',
      },
      timeline_days: {
        type: 'number',
        description: 'Number of days for timeline (default: 30)',
      },
    },
  },
};

const DashboardSchema = z.object({
  sections: z.array(z.enum(['overview', 'timeline', 'entities', 'projects', 'usage'])).optional(),
  timeline_days: z.number().min(1).max(365).default(30),
});

export async function handleMemoryDashboard(args: unknown) {
  const params = DashboardSchema.parse(args || {});

  const sections = params.sections || ['overview', 'timeline', 'entities', 'projects', 'usage'];

  logger.info(`Generating dashboard:  ${sections.join(', ')}`);

  try {
    const script = `
import sys
sys.path.append('python')

from analytics.dashboard_service import DashboardService
import sqlite3
import json
import os

db_path = os.getenv('MCP_MEMORY_DB_PATH', 'data/memories.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

service = DashboardService(conn)

dashboard = {}

sections = ${JSON.stringify(sections)}

if 'overview' in sections:
    dashboard['overview'] = service.get_overview()

if 'timeline' in sections: 
    dashboard['timeline'] = service.get_activity_timeline(${params.timeline_days})

if 'entities' in sections: 
    dashboard['top_entities'] = service.get_top_entities(20)

if 'projects' in sections:
    dashboard['projects'] = service.get_project_breakdown()

if 'usage' in sections:
    dashboard['usage'] = service.get_usage_stats()

print(json.dumps(dashboard, default=str))
conn.close()
`;

    const result = await runPythonScript(script);
    const dashboard = JSON.parse(result);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              generated_at: new Date().toISOString(),
              sections: sections,
              data: dashboard,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    logger.error('Dashboard generation failed:', error);
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
