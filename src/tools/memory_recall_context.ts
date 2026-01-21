/**
 * Memory Recall Context Tool
 * Proactively recalls relevant memories based on current context
 */

import { z } from 'zod';
import { logger } from '../utils/logger.js';
import { getDatabase } from '../storage/database.js';
import Database from 'better-sqlite3';

// Input schema for the tool
export const memoryRecallContextSchema = z.object({
  project: z.string().optional().describe('Optional project name to focus on'),
  file_path: z.string().optional().describe('Optional file path to focus on'),
  recent_minutes: z.number().default(30).describe('Time window for recent activity (default: 30)'),
  limit: z.number().default(10).describe('Maximum memories to recall (default: 10)'),
});

export type MemoryRecallContextInput = z.infer<typeof memoryRecallContextSchema>;

export interface ContextAnalysis {
  active: boolean;
  context_type: string | null;
  primary_project: string | null;
  active_projects: string[];
  active_entities: string[];
  current_focus: string | null;
  recent_activity_count: number;
}

export interface RecalledMemory {
  id: string;
  type: string;
  content: string;
  project: string | null;
  relevance_score: number;
  recall_reason: string;
}

export interface RecallContextResult {
  context: ContextAnalysis;
  recalled_memories: RecalledMemory[];
  suggestions: string[];
}

/**
 * Analyze current context and recall relevant memories
 */
export async function recallContext(input: MemoryRecallContextInput): Promise<RecallContextResult> {
  const db = getDatabase();

  try {
    // Calculate time window
    const cutoffTime = Date.now() - input.recent_minutes * 60 * 1000;

    // Build query for recent memories
    let query = `
      SELECT id, type, project, file_path, tags, entities, content, timestamp
      FROM memories
      WHERE timestamp > ? AND archived = 0
    `;
    const params: (string | number)[] = [cutoffTime];

    if (input.project) {
      query += ' AND project = ?';
      params.push(input.project);
    }

    if (input.file_path) {
      query += ' AND file_path LIKE ?';
      params.push(`%${input.file_path}%`);
    }

    query += ' ORDER BY timestamp DESC LIMIT 50';

    const recentMemories = db.prepare(query).all(...params) as {
      project: string | null;
      type: string | null;
      content: string | null;
      entities: string | null;
      file_path: string | null;
    }[];

    // Analyze context
    const context = analyzeContext(recentMemories, input.recent_minutes);

    if (!context.active) {
      return {
        context,
        recalled_memories: [],
        suggestions: ['No recent activity detected. Start working to build context.'],
      };
    }

    // Recall relevant memories
    const recalledMemories = await recallRelevantMemories(db, context, cutoffTime, input.limit);

    // Generate suggestions
    const suggestions = generateContextSuggestions(context, recalledMemories);

    logger.info(`Context recall: found ${recalledMemories.length} relevant memories`);

    return {
      context,
      recalled_memories: recalledMemories,
      suggestions,
    };
  } catch (error) {
    logger.error('Context recall failed', { error });
    throw error;
  }
}

/**
 * Analyze recent memories to understand current context
 */
function analyzeContext(
  recentMemories: {
    project: string | null;
    type: string | null;
    content: string | null;
    entities: string | null;
    file_path: string | null;
  }[],
  _recentMinutes: number
): ContextAnalysis {
  if (recentMemories.length === 0) {
    return {
      active: false,
      context_type: null,
      primary_project: null,
      active_projects: [],
      active_entities: [],
      current_focus: null,
      recent_activity_count: 0,
    };
  }

  // Count projects
  const projectCounts: Record<string, number> = {};
  const entityCounts: Record<string, number> = {};
  const typeCounts: Record<string, number> = {};

  for (const memory of recentMemories) {
    // Count projects
    if (memory.project) {
      projectCounts[memory.project] = (projectCounts[memory.project] || 0) + 1;
    }

    // Count types
    if (memory.type) {
      typeCounts[memory.type] = (typeCounts[memory.type] || 0) + 1;
    }

    // Count entities
    if (memory.entities) {
      try {
        const entities = JSON.parse(memory.entities);
        for (const entity of entities) {
          entityCounts[entity] = (entityCounts[entity] || 0) + 1;
        }
      } catch {
        // Skip invalid JSON
      }
    }
  }

  // Get top items
  const sortedProjects = Object.entries(projectCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([k]) => k);

  const sortedEntities = Object.entries(entityCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([k]) => k);

  // Infer context type
  const contextType = inferContextType(typeCounts, recentMemories);

  // Infer focus
  const currentFocus = inferFocus(recentMemories, entityCounts);

  return {
    active: true,
    context_type: contextType,
    primary_project: sortedProjects[0] || null,
    active_projects: sortedProjects.slice(0, 3),
    active_entities: sortedEntities,
    current_focus: currentFocus,
    recent_activity_count: recentMemories.length,
  };
}

/**
 * Infer context type from memory types and content
 */
function inferContextType(
  typeCounts: Record<string, number>,
  recentMemories: { content: string | null }[]
): string {
  const primaryType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0];

  // Check content for debugging patterns
  const allContent = recentMemories
    .slice(0, 10)
    .map((m) => (m.content || '').toLowerCase().slice(0, 200))
    .join(' ');

  const errorKeywords = ['error', 'exception', 'traceback', 'failed', 'bug', 'fix'];
  if (errorKeywords.some((kw) => allContent.includes(kw))) {
    return 'debugging';
  }

  const typeMap: Record<string, string> = {
    code: 'coding',
    command: 'system_admin',
    conversation: 'planning',
    note: 'documentation',
    decision: 'planning',
    insight: 'analysis',
  };

  return typeMap[primaryType || ''] || 'general';
}

/**
 * Infer current focus area
 */
function inferFocus(
  recentMemories: { file_path: string | null }[],
  entityCounts: Record<string, number>
): string | null {
  if (recentMemories.length === 0) return null;

  // Check top entity
  const topEntity = Object.entries(entityCounts).sort((a, b) => b[1] - a[1])[0];

  if (topEntity && topEntity[1] >= 3) {
    return `entity:${topEntity[0]}`;
  }

  // Check file focus
  const fileCounts: Record<string, number> = {};
  for (const memory of recentMemories) {
    if (memory.file_path) {
      fileCounts[memory.file_path] = (fileCounts[memory.file_path] || 0) + 1;
    }
  }

  const topFile = Object.entries(fileCounts).sort((a, b) => b[1] - a[1])[0];

  if (topFile && topFile[1] >= 3) {
    return `file:${topFile[0]}`;
  }

  return null;
}

/**
 * Recall memories relevant to current context
 */
async function recallRelevantMemories(
  db: Database.Database,
  context: ContextAnalysis,
  excludeCutoff: number,
  limit: number
): Promise<RecalledMemory[]> {
  const conditions: string[] = [];
  const params: (string | number)[] = [];

  // Match active projects
  if (context.active_projects.length > 0) {
    const placeholders = context.active_projects.map(() => '?').join(',');
    conditions.push(`project IN (${placeholders})`);
    params.push(...context.active_projects);
  }

  // Match active entities (top 5)
  if (context.active_entities.length > 0) {
    const entityConditions = context.active_entities.slice(0, 5).map(() => 'entities LIKE ?');
    conditions.push(`(${entityConditions.join(' OR ')})`);
    params.push(...context.active_entities.slice(0, 5).map((e) => `%${e}%`));
  }

  // Exclude recent memories
  conditions.push('timestamp < ?');
  params.push(excludeCutoff);

  // Only non-archived
  conditions.push('archived = 0');

  if (conditions.length === 0) {
    return [];
  }

  const query = `
    SELECT id, type, content, project, file_path, entities,
           importance_score, access_count
    FROM memories
    WHERE ${conditions.join(' AND ')}
    ORDER BY importance_score DESC, access_count DESC, timestamp DESC
    LIMIT ?
  `;
  params.push(limit * 2);

  const memories = db.prepare(query).all(...params) as {
    id: string;
    type: string;
    content: string | null;
    project: string | null;
    file_path: string | null;
    entities: string | null;
    importance_score: number;
    access_count: number;
  }[];

  // Score and format results
  const scored = memories.map((memory) => ({
    id: memory.id,
    type: memory.type,
    content: memory.content?.slice(0, 300) || '',
    project: memory.project,
    relevance_score: calculateRelevance(memory, context),
    recall_reason: getRecallReason(memory, context),
  }));

  // Sort by relevance and limit
  scored.sort((a, b) => b.relevance_score - a.relevance_score);

  return scored.slice(0, limit);
}

/**
 * Calculate relevance score
 */
function calculateRelevance(
  memory: {
    project: string | null;
    entities: string | null;
    importance_score: number;
    access_count: number;
  },
  context: ContextAnalysis
): number {
  let score = 0;

  // Project match
  if (memory.project === context.primary_project) {
    score += 0.35;
  } else if (memory.project && context.active_projects.includes(memory.project)) {
    score += 0.2;
  }

  // Entity overlap
  if (memory.entities && context.active_entities.length > 0) {
    try {
      const memoryEntities = new Set(JSON.parse(memory.entities));
      const overlap = context.active_entities.filter((e) => memoryEntities.has(e)).length;
      score += Math.min(0.3, overlap * 0.1);
    } catch {
      // Skip
    }
  }

  // Importance
  score += (memory.importance_score || 0.5) * 0.2;

  // Access count
  const accessNorm = Math.min(1, (memory.access_count || 0) / 10);
  score += accessNorm * 0.1;

  return Math.round(score * 1000) / 1000;
}

/**
 * Generate recall reason
 */
function getRecallReason(
  memory: {
    project: string | null;
    entities: string | null;
    importance_score: number;
  },
  context: ContextAnalysis
): string {
  const reasons: string[] = [];

  if (memory.project && memory.project === context.primary_project) {
    reasons.push(`Same project: ${memory.project}`);
  }

  if (memory.entities && context.active_entities.length > 0) {
    try {
      const memoryEntities = new Set(JSON.parse(memory.entities));
      const overlap = context.active_entities.filter((e) => memoryEntities.has(e));
      if (overlap.length > 0) {
        reasons.push(`Related entities: ${overlap.slice(0, 3).join(', ')}`);
      }
    } catch {
      // Skip
    }
  }

  if ((memory.importance_score || 0) >= 0.7) {
    reasons.push('High importance');
  }

  return reasons.length > 0 ? reasons.join('; ') : 'General relevance';
}

/**
 * Generate context-aware suggestions
 */
function generateContextSuggestions(
  context: ContextAnalysis,
  recalled: RecalledMemory[]
): string[] {
  const suggestions: string[] = [];

  if (context.context_type === 'debugging') {
    suggestions.push('Consider checking past error resolutions for similar issues.');
  }

  if (recalled.length > 0) {
    const highRelevance = recalled.filter((m) => m.relevance_score > 0.5);
    if (highRelevance.length > 0) {
      suggestions.push(`Found ${highRelevance.length} highly relevant past memories.`);
    }
  }

  if (context.current_focus) {
    const [type, value] = context.current_focus.split(':');
    if (type === 'entity') {
      suggestions.push(`Deep focus on "${value}" detected. Related memories recalled.`);
    }
  }

  return suggestions;
}

// Tool definition for MCP
export const memoryRecallContextTool = {
  name: 'memory_recall_context',
  description:
    'Proactively analyzes current work context and recalls relevant memories. Use this to get context-aware memory suggestions without explicit searching.',
  inputSchema: memoryRecallContextSchema,
  handler: recallContext,
};
