import { getDatabase } from '../storage/database.js';
import { logger } from '../utils/logger.js';
import { z } from 'zod';
import Database from 'better-sqlite3';

export const MEMORY_INSIGHTS_TOOL = {
  name: 'memory_insights',
  description:
    'Get insights and analytics about stored memories. Returns statistics about memory distribution, top entities, recent patterns, and memory health metrics.',
  inputSchema: {
    type: 'object',
    properties: {
      insight_type: {
        type: 'string',
        enum: ['overview', 'entities', 'patterns', 'health', 'trends'],
        description: 'Type of insights to retrieve',
      },
      time_window: {
        type: 'string',
        enum: ['day', 'week', 'month', 'all'],
        description: 'Time window for analysis (default: week)',
      },
      limit: {
        type: 'number',
        description: 'Maximum number of results for lists (default: 10)',
      },
    },
    required: ['insight_type'],
  },
};

const InsightsSchema = z.object({
  insight_type: z.enum(['overview', 'entities', 'patterns', 'health', 'trends']),
  time_window: z.enum(['day', 'week', 'month', 'all']).default('week'),
  limit: z.number().min(1).max(100).default(10),
});

export async function handleMemoryInsights(args: unknown) {
  const params = InsightsSchema.parse(args);

  logger.info(`Generating ${params.insight_type} insights for ${params.time_window}`);

  const db = getDatabase();

  // Calculate time window
  const now = Date.now();
  const timeWindowMs = {
    day: 24 * 60 * 60 * 1000,
    week: 7 * 24 * 60 * 60 * 1000,
    month: 30 * 24 * 60 * 60 * 1000,
    all: Number.MAX_SAFE_INTEGER,
  };

  const cutoffTime = now - timeWindowMs[params.time_window];

  let insights: Record<string, unknown> = {};

  try {
    switch (params.insight_type) {
      case 'overview':
        insights = await generateOverview(db, cutoffTime);
        break;

      case 'entities':
        insights = await generateEntityInsights(db, params.limit);
        break;

      case 'patterns':
        insights = await generatePatterns(db, cutoffTime, params.limit);
        break;

      case 'health':
        insights = await generateHealthMetrics(db);
        break;

      case 'trends':
        insights = await generateTrends(db, cutoffTime);
        break;
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              insight_type: params.insight_type,
              time_window: params.time_window,
              generated_at: new Date().toISOString(),
              insights,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    logger.error('Error generating insights:', error);
    throw error;
  }
}

async function generateOverview(db: Database.Database, cutoffTime: number) {
  // Total memories
  const total = db.prepare('SELECT COUNT(*) as count FROM memories WHERE archived = 0').get() as {
    count: number;
  };

  // By tier
  const byTier = db
    .prepare('SELECT tier, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY tier')
    .all() as { tier: string; count: number }[];

  // By type
  const byType = db
    .prepare('SELECT type, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY type')
    .all() as { type: string; count: number }[];

  // Recent activity
  const recentCount = db
    .prepare('SELECT COUNT(*) as count FROM memories WHERE timestamp > ? AND archived = 0')
    .get(cutoffTime) as { count: number };

  // Average importance
  const avgImportance = db
    .prepare('SELECT AVG(importance_score) as avg FROM memories WHERE archived = 0')
    .get() as { avg: number };

  // Total entities
  const totalEntities = db.prepare('SELECT COUNT(*) as count FROM entities').get() as {
    count: number;
  };

  return {
    total_memories: total.count,
    recent_memories: recentCount.count,
    avg_importance: parseFloat(avgImportance.avg?.toFixed(2) || '0'),
    by_tier: byTier.map((row) => ({
      tier: row.tier,
      count: row.count,
      percentage: ((row.count / total.count) * 100).toFixed(1) + '%',
    })),
    by_type: byType.map((row) => ({
      type: row.type,
      count: row.count,
      percentage: ((row.count / total.count) * 100).toFixed(1) + '%',
    })),
    total_entities: totalEntities.count,
  };
}

async function generateEntityInsights(db: Database.Database, limit: number) {
  // Top entities by mention count
  const topEntities = db
    .prepare(
      `
    SELECT type, name, mention_count, first_seen, last_seen
    FROM entities
    ORDER BY mention_count DESC
    LIMIT ?
  `
    )
    .all(limit) as {
    type: string;
    name: string;
    mention_count: number;
    first_seen: number;
    last_seen: number;
  }[];

  // Entities by type
  const byType = db.prepare('SELECT type, COUNT(*) as count FROM entities GROUP BY type').all() as {
    type: string;
    count: number;
  }[];

  // Recent entities
  const recentEntities = db
    .prepare(
      `
    SELECT type, name, mention_count, first_seen
    FROM entities
    ORDER BY first_seen DESC
    LIMIT ? 
  `
    )
    .all(limit) as {
    type: string;
    name: string;
    mention_count: number;
    first_seen: number;
  }[];

  // Entity relationships
  const relationshipCount = db
    .prepare('SELECT COUNT(*) as count FROM entity_relationships')
    .get() as { count: number };

  return {
    top_entities: topEntities.map((e) => ({
      type: e.type,
      name: e.name,
      mentions: e.mention_count,
      first_seen: new Date(e.first_seen * 1000).toISOString(),
      last_seen: new Date(e.last_seen * 1000).toISOString(),
    })),
    by_type: byType,
    recent_entities: recentEntities.map((e) => ({
      type: e.type,
      name: e.name,
      mentions: e.mention_count,
      first_seen: new Date(e.first_seen * 1000).toISOString(),
    })),
    total_relationships: relationshipCount.count,
  };
}

async function generatePatterns(db: Database.Database, cutoffTime: number, limit: number) {
  // Most accessed memories
  const mostAccessed = db
    .prepare(
      `
    SELECT id, type, content, access_count, importance_score
    FROM memories
    WHERE archived = 0 AND timestamp > ?
    ORDER BY access_count DESC
    LIMIT ?
  `
    )
    .all(cutoffTime, limit) as {
    id: string;
    type: string;
    content: string;
    access_count: number;
    importance_score: number;
  }[];

  // Projects by memory count
  const topProjects = db
    .prepare(
      `
    SELECT project, COUNT(*) as count
    FROM memories
    WHERE project IS NOT NULL AND archived = 0
    GROUP BY project
    ORDER BY count DESC
    LIMIT ? 
  `
    )
    .all(limit) as { project: string; count: number }[];

  // Common tags
  const allTags = db
    .prepare(
      `
    SELECT tags
    FROM memories
    WHERE tags IS NOT NULL AND tags != '[]' AND archived = 0
  `
    )
    .all() as { tags: string }[];

  const tagCounts: Record<string, number> = {};
  for (const row of allTags) {
    try {
      const tags = JSON.parse(row.tags);
      for (const tag of tags) {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
      }
    } catch {
      // Skip invalid JSON
    }
  }

  const topTags = Object.entries(tagCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, limit)
    .map(([tag, count]) => ({ tag, count }));

  return {
    most_accessed: mostAccessed.map((m) => ({
      id: m.id,
      type: m.type,
      preview: m.content.substring(0, 100) + (m.content.length > 100 ? '...' : ''),
      access_count: m.access_count,
      importance: m.importance_score,
    })),
    top_projects: topProjects,
    top_tags: topTags,
  };
}

async function generateHealthMetrics(db: Database.Database) {
  // Memory distribution health
  const tierDistribution = db
    .prepare('SELECT tier, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY tier')
    .all() as { tier: string; count: number }[];

  const total = tierDistribution.reduce((sum: number, t) => sum + t.count, 0);

  // Low-importance memories
  const lowImportance = db
    .prepare('SELECT COUNT(*) as count FROM memories WHERE importance_score < 0.3 AND archived = 0')
    .get() as { count: number };

  // Unaccessed memories
  const unaccessed = db
    .prepare('SELECT COUNT(*) as count FROM memories WHERE access_count = 0 AND archived = 0')
    .get() as { count: number };

  // Memories without entities
  const noEntities = db
    .prepare(
      "SELECT COUNT(*) as count FROM memories WHERE (entities IS NULL OR entities = '[]') AND archived = 0"
    )
    .get() as { count: number };

  // Storage usage estimate
  const storageStats = db
    .prepare('SELECT SUM(LENGTH(content)) as total_chars FROM memories WHERE archived = 0')
    .get() as { total_chars: number };

  const estimatedMB = (storageStats.total_chars / (1024 * 1024)).toFixed(2);

  // Calculate health score (0-100)
  let healthScore = 100;

  // Penalize if too many short-term memories
  const shortTerm = tierDistribution.find((t) => t.tier === 'short');
  if (shortTerm && shortTerm.count / total > 0.7) {
    healthScore -= 20; // Too many short-term memories
  }

  // Penalize if many low-importance
  if (lowImportance.count / total > 0.5) {
    healthScore -= 15;
  }

  // Penalize if many unaccessed
  if (unaccessed.count / total > 0.6) {
    healthScore -= 15;
  }

  // Penalize if many without entities
  if (noEntities.count / total > 0.5) {
    healthScore -= 10;
  }

  return {
    health_score: Math.max(0, healthScore),
    tier_distribution: tierDistribution.map((t) => ({
      tier: t.tier,
      count: t.count,
      percentage: ((t.count / total) * 100).toFixed(1) + '%',
    })),
    issues: {
      low_importance_count: lowImportance.count,
      unaccessed_count: unaccessed.count,
      missing_entities_count: noEntities.count,
    },
    storage: {
      estimated_mb: estimatedMB,
      total_memories: total,
    },
    recommendations: generateRecommendations(healthScore, {
      lowImportance: lowImportance.count / total,
      unaccessed: unaccessed.count / total,
      shortTerm: shortTerm ? shortTerm.count / total : 0,
    }),
  };
}

async function generateTrends(db: Database.Database, cutoffTime: number) {
  // Memories created over time (daily)
  const dailyCreation = db
    .prepare(
      `
    SELECT DATE(timestamp / 1000, 'unixepoch') as date, COUNT(*) as count
    FROM memories
    WHERE timestamp > ?
    GROUP BY date
    ORDER BY date DESC
    LIMIT 30
  `
    )
    .all(cutoffTime) as { date: string; count: number }[];

  // Average importance trend
  const importanceTrend = db
    .prepare(
      `
    SELECT tier, AVG(importance_score) as avg_importance
    FROM memories
    WHERE archived = 0
    GROUP BY tier
  `
    )
    .all() as { tier: string; avg_importance: number }[];

  // Growth rate
  const oldCount = db
    .prepare('SELECT COUNT(*) as count FROM memories WHERE timestamp < ? AND archived = 0')
    .get(cutoffTime) as { count: number };

  const newCount = db
    .prepare('SELECT COUNT(*) as count FROM memories WHERE timestamp >= ? AND archived = 0')
    .get(cutoffTime) as { count: number };

  const growthRate =
    oldCount.count > 0 ? ((newCount.count / oldCount.count) * 100).toFixed(1) : 'N/A';

  return {
    daily_creation: dailyCreation,
    importance_by_tier: importanceTrend,
    growth: {
      previous_period: oldCount.count,
      current_period: newCount.count,
      growth_rate: growthRate + '%',
    },
  };
}

function generateRecommendations(
  healthScore: number,
  metrics: { lowImportance: number; unaccessed: number; shortTerm: number }
): string[] {
  const recommendations: string[] = [];

  if (healthScore < 60) {
    recommendations.push('Overall memory health is low. Consider running cleanup and promotion.');
  }

  if (metrics.shortTerm > 0.7) {
    recommendations.push(
      'High proportion of short-term memories. Run memory_promoter to organize into tiers.'
    );
  }

  if (metrics.lowImportance > 0.5) {
    recommendations.push(
      'Many low-importance memories detected. Consider archiving or deleting unused memories.'
    );
  }

  if (metrics.unaccessed > 0.6) {
    recommendations.push(
      'Many memories have never been accessed. Review relevance and importance scoring.'
    );
  }

  if (recommendations.length === 0) {
    recommendations.push('Memory system is healthy. Continue regular maintenance.');
  }

  return recommendations;
}
