/**
 * Memory Analytics Tool
 * Provides advanced analytics on memory data including graph analysis and patterns
 */

import { z } from 'zod';
import { logger } from '../utils/logger.js';
import { getDatabase } from '../storage/database.js';

// Input schema for the tool
export const memoryAnalyticsSchema = z.object({
  query_type: z
    .enum(['graph', 'patterns', 'statistics', 'trends', 'entities'])
    .describe('Type of analytics query'),
  project: z.string().optional().describe('Optional project filter'),
  entity: z.string().optional().describe('Entity for entity-specific queries'),
  days: z.number().default(30).describe('Number of days to analyze (default: 30)'),
  limit: z.number().default(10).describe('Maximum results (default: 10)'),
});

export type MemoryAnalyticsInput = z.infer<typeof memoryAnalyticsSchema>;

export interface GraphStatistics {
  node_count: number;
  edge_count: number;
  density: number;
  connected: boolean;
  num_components?: number;
  central_entities: EntityInfo[];
  bridging_entities: EntityInfo[];
}

export interface EntityInfo {
  id: string;
  name: string;
  type: string;
  score: number;
}

export interface PatternInfo {
  type: string;
  description: string;
  frequency: number;
  entities?: string[];
}

export interface TrendInfo {
  direction: 'increasing' | 'decreasing' | 'stable';
  ratio: number;
  period_counts: number[];
}

export interface AnalyticsResult {
  query_type: string;
  data: any;
  summary: string;
}

/**
 * Execute analytics query
 */
export async function getAnalytics(input: MemoryAnalyticsInput): Promise<AnalyticsResult> {
  const db = getDatabase();

  try {
    let result: AnalyticsResult;

    switch (input.query_type) {
      case 'graph':
        result = await getGraphAnalytics(db, input.limit);
        break;
      case 'patterns':
        result = await getPatternAnalytics(db, input.days, input.limit);
        break;
      case 'statistics':
        result = await getStatistics(db);
        break;
      case 'trends':
        result = await getTrendAnalytics(db, input.project, input.entity, input.days);
        break;
      case 'entities':
        result = await getEntityAnalytics(db, input.entity, input.limit);
        break;
      default:
        throw new Error(`Unknown query type: ${input.query_type}`);
    }

    logger.info(`Analytics query: ${input.query_type}`);

    return result;
  } catch (error) {
    logger.error('Analytics query failed', { error, queryType: input.query_type });
    throw error;
  }
}

/**
 * Get graph analytics
 */
async function getGraphAnalytics(db: any, limit: number): Promise<AnalyticsResult> {
  // Get entity count
  const entityCount = db.prepare('SELECT COUNT(*) as count FROM entities').get() as any;

  // Get relationship count
  const relCount = db.prepare('SELECT COUNT(*) as count FROM entity_relationships').get() as any;

  // Get central entities (by mention count)
  const centralEntities = db
    .prepare(
      `
    SELECT id, name, type, mention_count
    FROM entities
    ORDER BY mention_count DESC
    LIMIT ?
  `
    )
    .all(limit) as any[];

  // Get bridging entities (entities with most relationships)
  const bridgingQuery = `
    SELECT e.id, e.name, e.type, 
           (SELECT COUNT(*) FROM entity_relationships 
            WHERE source_id = e.id OR target_id = e.id) as rel_count
    FROM entities e
    ORDER BY rel_count DESC
    LIMIT ?
  `;
  const bridgingEntities = db.prepare(bridgingQuery).all(limit) as any[];

  // Calculate density (if we can)
  const nodeCount = entityCount.count || 0;
  const edgeCount = relCount.count || 0;
  const maxEdges = nodeCount > 1 ? (nodeCount * (nodeCount - 1)) / 2 : 1;
  const density = maxEdges > 0 ? edgeCount / maxEdges : 0;

  const data: GraphStatistics = {
    node_count: nodeCount,
    edge_count: edgeCount,
    density: Math.round(density * 10000) / 10000,
    connected: nodeCount <= 1 || edgeCount > 0,
    central_entities: centralEntities.map((e) => ({
      id: e.id,
      name: e.name,
      type: e.type,
      score: e.mention_count,
    })),
    bridging_entities: bridgingEntities.map((e) => ({
      id: e.id,
      name: e.name,
      type: e.type,
      score: e.rel_count,
    })),
  };

  return {
    query_type: 'graph',
    data,
    summary: `Knowledge graph contains ${nodeCount} entities and ${edgeCount} relationships.`,
  };
}

/**
 * Get pattern analytics
 */
async function getPatternAnalytics(db: any, days: number, limit: number): Promise<AnalyticsResult> {
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;

  // Get entity co-occurrence patterns
  const memories = db
    .prepare(
      `
    SELECT entities
    FROM memories
    WHERE timestamp > ? AND archived = 0 AND entities IS NOT NULL
  `
    )
    .all(cutoff) as any[];

  const pairCounts: Record<string, number> = {};

  for (const memory of memories) {
    try {
      const entities = JSON.parse(memory.entities);
      if (entities.length >= 2) {
        for (let i = 0; i < entities.length; i++) {
          for (let j = i + 1; j < entities.length; j++) {
            const pair = [entities[i], entities[j]].sort().join('::');
            pairCounts[pair] = (pairCounts[pair] || 0) + 1;
          }
        }
      }
    } catch {
      // Skip invalid JSON
    }
  }

  // Get top patterns
  const patterns: PatternInfo[] = Object.entries(pairCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .filter(([, count]) => count >= 2)
    .map(([pair, count]) => ({
      type: 'entity_co_occurrence',
      entities: pair.split('::'),
      frequency: count,
      description: `Entities "${pair.replace('::', '" and "')}" frequently appear together`,
    }));

  // Get time patterns
  const hourCounts: Record<number, number> = {};
  const allMemories = db
    .prepare(
      `
    SELECT timestamp
    FROM memories
    WHERE timestamp > ? AND archived = 0
  `
    )
    .all(cutoff) as any[];

  for (const m of allMemories) {
    const hour = new Date(m.timestamp).getHours();
    hourCounts[hour] = (hourCounts[hour] || 0) + 1;
  }

  const peakHour = Object.entries(hourCounts).sort((a, b) => b[1] - a[1])[0];

  if (peakHour) {
    patterns.push({
      type: 'peak_activity_hour',
      description: `Most active hour: ${peakHour[0]}:00-${parseInt(peakHour[0]) + 1}:00`,
      frequency: peakHour[1],
    });
  }

  return {
    query_type: 'patterns',
    data: { patterns, analysis_period_days: days },
    summary: `Found ${patterns.length} patterns in the last ${days} days.`,
  };
}

/**
 * Get overall statistics
 */
async function getStatistics(db: any): Promise<AnalyticsResult> {
  // Total memories
  const totalMemories = db
    .prepare('SELECT COUNT(*) as count FROM memories WHERE archived = 0')
    .get() as any;

  // Archived memories
  const archivedMemories = db
    .prepare('SELECT COUNT(*) as count FROM memories WHERE archived = 1')
    .get() as any;

  // By type
  const byType = db
    .prepare(
      `
    SELECT type, COUNT(*) as count
    FROM memories
    WHERE archived = 0
    GROUP BY type
    ORDER BY count DESC
  `
    )
    .all() as any[];

  // By project
  const byProject = db
    .prepare(
      `
    SELECT project, COUNT(*) as count
    FROM memories
    WHERE archived = 0 AND project IS NOT NULL
    GROUP BY project
    ORDER BY count DESC
    LIMIT 10
  `
    )
    .all() as any[];

  // By tier
  const byTier = db
    .prepare(
      `
    SELECT tier, COUNT(*) as count
    FROM memories
    WHERE archived = 0
    GROUP BY tier
  `
    )
    .all() as any[];

  // Entities
  const entityCount = db.prepare('SELECT COUNT(*) as count FROM entities').get() as any;

  // Relationships
  const relCount = db.prepare('SELECT COUNT(*) as count FROM entity_relationships').get() as any;

  // Average importance
  const avgImportance = db
    .prepare(
      `
    SELECT AVG(importance_score) as avg
    FROM memories
    WHERE archived = 0
  `
    )
    .get() as any;

  // Last 24h activity
  const dayAgo = Date.now() - 24 * 60 * 60 * 1000;
  const recentActivity = db
    .prepare(
      `
    SELECT COUNT(*) as count
    FROM memories
    WHERE timestamp > ? AND archived = 0
  `
    )
    .get(dayAgo) as any;

  const data = {
    total_active_memories: totalMemories.count,
    total_archived_memories: archivedMemories.count,
    memories_by_type: Object.fromEntries(byType.map((r) => [r.type, r.count])),
    memories_by_tier: Object.fromEntries(byTier.map((r) => [r.tier, r.count])),
    top_projects: Object.fromEntries(byProject.map((r) => [r.project, r.count])),
    total_entities: entityCount.count,
    total_relationships: relCount.count,
    avg_importance: Math.round((avgImportance.avg || 0) * 1000) / 1000,
    activity_last_24h: recentActivity.count,
  };

  return {
    query_type: 'statistics',
    data,
    summary: `${totalMemories.count} active memories, ${entityCount.count} entities, ${recentActivity.count} new in last 24h.`,
  };
}

/**
 * Get trend analytics
 */
async function getTrendAnalytics(
  db: any,
  project?: string,
  entity?: string,
  days: number = 30
): Promise<AnalyticsResult> {
  const periodDays = Math.floor(days / 4);
  const periodCounts: number[] = [];

  for (let i = 3; i >= 0; i--) {
    const periodEnd = Date.now() - i * periodDays * 24 * 60 * 60 * 1000;
    const periodStart = Date.now() - (i + 1) * periodDays * 24 * 60 * 60 * 1000;

    let query =
      'SELECT COUNT(*) as count FROM memories WHERE timestamp > ? AND timestamp <= ? AND archived = 0';
    const params: any[] = [periodStart, periodEnd];

    if (entity) {
      query += ' AND entities LIKE ?';
      params.push(`%${entity}%`);
    }

    if (project) {
      query += ' AND project = ?';
      params.push(project);
    }

    const result = db.prepare(query).get(...params) as any;
    periodCounts.push(result.count);
  }

  // Calculate trend
  let direction: 'increasing' | 'decreasing' | 'stable' = 'stable';
  let ratio = 0;

  if (periodCounts[0] > 0) {
    ratio = (periodCounts[3] - periodCounts[0]) / periodCounts[0];

    if (ratio > 0.3) {
      direction = 'increasing';
    } else if (ratio < -0.3) {
      direction = 'decreasing';
    }
  }

  const data: TrendInfo = {
    direction,
    ratio: Math.round(ratio * 1000) / 1000,
    period_counts: periodCounts,
  };

  const subject = entity || project || 'overall activity';

  return {
    query_type: 'trends',
    data: {
      ...data,
      entity,
      project,
      period_days: days,
      total_count: periodCounts.reduce((a, b) => a + b, 0),
    },
    summary: `${subject} is ${direction} (${(ratio * 100).toFixed(1)}% change over ${days} days).`,
  };
}

/**
 * Get entity-specific analytics
 */
async function getEntityAnalytics(
  db: any,
  entityName?: string,
  limit: number = 10
): Promise<AnalyticsResult> {
  if (entityName) {
    // Specific entity analysis
    const entity = db
      .prepare(
        `
      SELECT * FROM entities WHERE name LIKE ? LIMIT 1
    `
      )
      .get(`%${entityName}%`) as any;

    if (!entity) {
      return {
        query_type: 'entities',
        data: { found: false, entity_name: entityName },
        summary: `Entity "${entityName}" not found.`,
      };
    }

    // Get related memories
    const memories = db
      .prepare(
        `
      SELECT m.id, m.type, m.content, m.project, m.timestamp
      FROM memories m
      WHERE m.entities LIKE ? AND m.archived = 0
      ORDER BY m.timestamp DESC
      LIMIT ?
    `
      )
      .all(`%${entity.name}%`, limit) as any[];

    // Get related entities
    const related = db
      .prepare(
        `
      SELECT e.id, e.name, e.type, er.strength
      FROM entity_relationships er
      JOIN entities e ON (e.id = er.target_id OR e.id = er.source_id)
      WHERE (er.source_id = ? OR er.target_id = ?) AND e.id != ?
      ORDER BY er.strength DESC
      LIMIT ?
    `
      )
      .all(entity.id, entity.id, entity.id, limit) as any[];

    return {
      query_type: 'entities',
      data: {
        entity: {
          id: entity.id,
          name: entity.name,
          type: entity.type,
          mention_count: entity.mention_count,
        },
        related_entities: related,
        recent_memories: memories.map((m) => ({
          id: m.id,
          type: m.type,
          project: m.project,
          content_preview: (m.content || '').slice(0, 100),
        })),
      },
      summary: `Entity "${entity.name}" has ${entity.mention_count} mentions and ${related.length} related entities.`,
    };
  } else {
    // Top entities overview
    const topEntities = db
      .prepare(
        `
      SELECT id, name, type, mention_count
      FROM entities
      ORDER BY mention_count DESC
      LIMIT ?
    `
      )
      .all(limit) as any[];

    // Entity type distribution
    const typeDistribution = db
      .prepare(
        `
      SELECT type, COUNT(*) as count
      FROM entities
      GROUP BY type
      ORDER BY count DESC
    `
      )
      .all() as any[];

    return {
      query_type: 'entities',
      data: {
        top_entities: topEntities,
        type_distribution: Object.fromEntries(typeDistribution.map((r) => [r.type, r.count])),
      },
      summary: `${topEntities.length} top entities returned. Most mentioned: ${topEntities[0]?.name || 'none'}.`,
    };
  }
}

// Tool definition for MCP
export const memoryAnalyticsTool = {
  name: 'memory_analytics',
  description:
    'Provides advanced analytics on memory data. Supports queries for graph analysis, pattern detection, statistics, trends, and entity analysis.',
  inputSchema: memoryAnalyticsSchema,
  handler: getAnalytics,
};
