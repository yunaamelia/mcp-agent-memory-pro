import { spawn } from 'child_process';
import { logger } from '../utils/logger.js';
import { z } from 'zod';

export const MEMORY_PROFILE_TOOL = {
  name: 'memory_profile',
  description:
    'Profile system performance, identify bottlenecks, and get optimization recommendations. Analyzes query performance, cache efficiency, and resource usage.',
  inputSchema: {
    type: 'object',
    properties: {
      profile_type: {
        type: 'string',
        enum: ['query_performance', 'cache_stats', 'resource_usage', 'all'],
        description: 'Type of profiling to perform',
      },
      duration_seconds: {
        type: 'number',
        description: 'Duration to profile (default: 10)',
      },
    },
    required: ['profile_type'],
  },
};

const ProfileSchema = z.object({
  profile_type: z.enum(['query_performance', 'cache_stats', 'resource_usage', 'all']),
  duration_seconds: z.number().min(1).max(60).default(10),
});

export async function handleMemoryProfile(args: unknown) {
  const params = ProfileSchema.parse(args);

  logger.info(`Profiling: ${params.profile_type}`);

  try {
    const script = `
import sys
sys.path.append('python')

import sqlite3
import json
import time
from pathlib import Path

results = {}

profile_type = '${params.profile_type}'

# Query Performance
if profile_type in ['query_performance', 'all']:
    conn = sqlite3.connect('data/memories.db')
    
    queries = [
        ('SELECT COUNT(*) FROM memories', 'count_memories'),
        ('SELECT * FROM memories ORDER BY importance_score DESC LIMIT 10', 'top_important'),
    ]
    
    query_perf = []
    
    for query, name in queries:
        start = time.time()
        try:
            conn.execute(query)
            duration = time.time() - start
            query_perf.append({
                'name': name,
                'duration_ms': round(duration * 1000, 2),
                'query': query[:50]
            })
        except:
            pass
    
    results['query_performance'] = query_perf
    conn.close()

# Cache Stats
if profile_type in ['cache_stats', 'all']:
    try:
        from caching.cache_manager import CacheManager
        cache = CacheManager('data/cache')
        stats = cache.get_stats()
        results['cache_stats'] = stats
    except Exception as e:
        results['cache_stats'] = {'error': str(e)}

# Resource Usage
if profile_type in ['resource_usage', 'all']:
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        results['resource_usage'] = {
            'cpu_percent': cpu_percent,
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_percent': memory.percent,
            'disk_total_gb': round(disk.total / (1024**3), 2),
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_percent': disk.percent
        }
    except ImportError:
        results['resource_usage'] = {'error': 'psutil not installed'}

# Generate recommendations
recommendations = []

if results.get('query_performance'):
    slow_queries = [q for q in results['query_performance'] if q['duration_ms'] > 100]
    if slow_queries:
        recommendations.append(f"Optimize {len(slow_queries)} slow queries")

if results.get('cache_stats'):
    cache_stats = results['cache_stats']
    if cache_stats.get('memory_size', 0) < 100:
        recommendations.append("Cache is underutilized - consider warming cache")

if results.get('resource_usage') and not results['resource_usage'].get('error'):
    if results['resource_usage']['memory_percent'] > 80:
        recommendations.append("High memory usage - consider increasing RAM")
    if results['resource_usage']['disk_percent'] > 90:
        recommendations.append("Disk space critical - clean up old data")

results['recommendations'] = recommendations

print(json.dumps(results, default=str))
`;

    const result = await runPythonScript(script);
    const data = JSON.parse(result);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              profile_type: params.profile_type,
              timestamp: new Date().toISOString(),
              profile_data: data,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    logger.error('Profiling failed:', error);
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
