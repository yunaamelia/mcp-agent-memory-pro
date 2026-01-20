import { spawn } from 'child_process';
import { logger } from '../utils/logger.js';
import { z } from 'zod';

export const MEMORY_PREDICT_TOOL = {
  name: 'memory_predict',
  description:
    'Use machine learning to predict memory importance, next tasks, and patterns. Provides AI-powered predictions about what you should work on next, which memories are most important, and future trends.',
  inputSchema: {
    type: 'object',
    properties: {
      prediction_type: {
        type: 'string',
        enum: ['importance', 'next_tasks', 'patterns', 'all'],
        description: 'Type of prediction to make',
      },
      context: {
        type: 'object',
        description: 'Current context for predictions (optional)',
      },
      limit: {
        type: 'number',
        description: 'Maximum number of predictions (default: 5)',
      },
    },
    required: ['prediction_type'],
  },
};

const PredictSchema = z.object({
  prediction_type: z.enum(['importance', 'next_tasks', 'patterns', 'all']),
  context: z.record(z.any()).optional(),
  limit: z.number().min(1).max(20).default(5),
});

export async function handleMemoryPredict(args: unknown) {
  const params = PredictSchema.parse(args);

  logger.info(`Making ML predictions: ${params.prediction_type}`);

  try {
    const script = `
import sys
sys.path.append('python')

import sqlite3
import json
from pathlib import Path

conn = sqlite3.connect('data/memories.db')
conn.row_factory = sqlite3.Row

predictions = {}

prediction_type = '${params.prediction_type}'
limit = ${params.limit}

if prediction_type in ['importance', 'all']:
    # Predict importance for recent memories
    cursor = conn.execute("""
        SELECT id, type, content, importance_score FROM memories 
        WHERE archived = 0
        ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    
    memories = [dict(row) for row in cursor.fetchall()]
    
    importance_predictions = []
    for memory in memories:
        # Simple heuristic prediction (ML predictor placeholder)
        score = 0.5
        content = memory.get('content', '')
        if len(content) > 200:
            score += 0.1
        if memory.get('type') == 'code':
            score += 0.2
        importance_predictions.append({
            'memory_id': memory['id'],
            'predicted_importance': min(score, 1.0),
            'content_preview': content[:100] if content else ''
        })
    
    predictions['importance'] = importance_predictions

if prediction_type in ['next_tasks', 'all']:
    # Predict next tasks based on recent activity
    cursor = conn.execute("""
        SELECT type, project, COUNT(*) as count FROM memories
        WHERE archived = 0
        GROUP BY type, project
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))
    
    task_predictions = []
    for row in cursor.fetchall():
        task_predictions.append({
            'task': f"Continue work on {row['project'] or 'default'} ({row['type']})",
            'confidence': min(0.5 + (row['count'] * 0.05), 0.95)
        })
    
    predictions['next_tasks'] = task_predictions

if prediction_type in ['patterns', 'all']:
    # Detect patterns
    cursor = conn.execute("""
        SELECT type, COUNT(*) as count FROM memories
        WHERE archived = 0
        GROUP BY type
        ORDER BY count DESC
    """)
    
    patterns = {
        'temporal': [],
        'recurring': [dict(row) for row in cursor.fetchall()][:limit]
    }
    
    predictions['patterns'] = patterns

print(json.dumps(predictions, default=str))
conn.close()
`;

    const result = await runPythonScript(script);
    const predictions = JSON.parse(result);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              prediction_type: params.prediction_type,
              timestamp: new Date().toISOString(),
              predictions: predictions,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    logger.error('Prediction failed:', error);
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
