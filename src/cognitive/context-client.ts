/**
 * Context Analysis Client
 * TypeScript client for context analysis services
 */

import { logger } from '../utils/logger.js';
import { getDatabase } from '../storage/database.js';

export interface ContextAnalysis {
  active: boolean;
  context_type: string | null;
  primary_project: string | null;
  active_projects: string[];
  active_entities: string[];
  active_files: string[];
  current_focus: string | null;
  recent_activity_count: number;
  time_window_minutes: number;
}

export interface RecalledMemory {
  id: string;
  type: string;
  content: string;
  project: string | null;
  relevance_score: number;
  recall_reason: string;
}

export interface ContextClientOptions {
  recentWindowMinutes?: number;
  recallLimit?: number;
}

/**
 * Client for context analysis operations
 */
export class ContextClient {
  private recentWindowMinutes: number;
  private recallLimit: number;

  constructor(options: ContextClientOptions = {}) {
    this.recentWindowMinutes = options.recentWindowMinutes ?? 30;
    this.recallLimit = options.recallLimit ?? 10;
  }

  /**
   * Analyze current context from recent activity
   */
  async analyzeContext(projectHint?: string, fileHint?: string): Promise<ContextAnalysis> {
    const db = getDatabase();
    const cutoffTime = Date.now() - this.recentWindowMinutes * 60 * 1000;

    try {
      // Build query
      let query = `
        SELECT id, type, project, file_path, tags, entities, content
        FROM memories
        WHERE timestamp > ? AND archived = 0
      `;
      const params: any[] = [cutoffTime];

      if (projectHint) {
        query += ' AND project = ?';
        params.push(projectHint);
      }

      if (fileHint) {
        query += ' AND file_path LIKE ?';
        params.push(`%${fileHint}%`);
      }

      query += ' ORDER BY timestamp DESC LIMIT 50';

      const recentMemories = db.prepare(query).all(...params) as any[];

      if (recentMemories.length === 0) {
        return {
          active: false,
          context_type: null,
          primary_project: null,
          active_projects: [],
          active_entities: [],
          active_files: [],
          current_focus: null,
          recent_activity_count: 0,
          time_window_minutes: this.recentWindowMinutes,
        };
      }

      // Extract patterns
      const projectCounts: Record<string, number> = {};
      const entityCounts: Record<string, number> = {};
      const typeCounts: Record<string, number> = {};
      const fileCounts: Record<string, number> = {};

      for (const memory of recentMemories) {
        if (memory.project) {
          projectCounts[memory.project] = (projectCounts[memory.project] || 0) + 1;
        }

        if (memory.type) {
          typeCounts[memory.type] = (typeCounts[memory.type] || 0) + 1;
        }

        if (memory.file_path) {
          fileCounts[memory.file_path] = (fileCounts[memory.file_path] || 0) + 1;
        }

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

      // Sort and extract top items
      const sortedProjects = Object.entries(projectCounts)
        .sort((a, b) => b[1] - a[1])
        .map(([k]) => k);

      const sortedEntities = Object.entries(entityCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([k]) => k);

      const sortedFiles = Object.entries(fileCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([k]) => k);

      // Infer context type
      const contextType = this.inferContextType(typeCounts, recentMemories);

      // Infer focus
      const currentFocus = this.inferFocus(recentMemories, fileCounts, entityCounts);

      return {
        active: true,
        context_type: contextType,
        primary_project: sortedProjects[0] || null,
        active_projects: sortedProjects.slice(0, 3),
        active_entities: sortedEntities,
        active_files: sortedFiles,
        current_focus: currentFocus,
        recent_activity_count: recentMemories.length,
        time_window_minutes: this.recentWindowMinutes,
      };
    } catch (error) {
      logger.error('Context analysis failed', { error });
      throw error;
    }
  }

  /**
   * Recall memories relevant to current context
   */
  async recallMemories(context?: ContextAnalysis, limit?: number): Promise<RecalledMemory[]> {
    // Get context if not provided
    if (!context) {
      context = await this.analyzeContext();
    }

    if (!context.active) {
      return [];
    }

    const db = getDatabase();
    const effectiveLimit = limit ?? this.recallLimit;
    const excludeCutoff = Date.now() - this.recentWindowMinutes * 60 * 1000;

    try {
      const conditions: string[] = [];
      const params: any[] = [];

      // Match active projects
      if (context.active_projects.length > 0) {
        const placeholders = context.active_projects.map(() => '?').join(',');
        conditions.push(`project IN (${placeholders})`);
        params.push(...context.active_projects);
      }

      // Match active entities
      if (context.active_entities.length > 0) {
        const entityConditions = context.active_entities.slice(0, 5).map(() => 'entities LIKE ?');
        conditions.push(`(${entityConditions.join(' OR ')})`);
        params.push(...context.active_entities.slice(0, 5).map((e) => `%${e}%`));
      }

      // Exclude recent
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
      params.push(effectiveLimit * 2);

      const memories = db.prepare(query).all(...params) as any[];

      // Score and format
      const scored = memories.map((memory) => ({
        id: memory.id,
        type: memory.type,
        content: (memory.content || '').slice(0, 300),
        project: memory.project,
        relevance_score: this.calculateRelevance(memory, context!),
        recall_reason: this.getRecallReason(memory, context!),
      }));

      // Sort and limit
      scored.sort((a, b) => b.relevance_score - a.relevance_score);

      return scored.slice(0, effectiveLimit);
    } catch (error) {
      logger.error('Memory recall failed', { error });
      throw error;
    }
  }

  /**
   * Infer context type from memory types and content
   */
  private inferContextType(typeCounts: Record<string, number>, recentMemories: any[]): string {
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
  private inferFocus(
    recentMemories: any[],
    fileCounts: Record<string, number>,
    entityCounts: Record<string, number>
  ): string | null {
    if (recentMemories.length === 0) return null;

    // Check top file
    const topFile = Object.entries(fileCounts).sort((a, b) => b[1] - a[1])[0];

    if (topFile && topFile[1] >= 3) {
      return `file:${topFile[0]}`;
    }

    // Check top entity
    const topEntity = Object.entries(entityCounts).sort((a, b) => b[1] - a[1])[0];

    if (topEntity && topEntity[1] >= 3) {
      return `entity:${topEntity[0]}`;
    }

    return null;
  }

  /**
   * Calculate relevance score
   */
  private calculateRelevance(memory: any, context: ContextAnalysis): number {
    let score = 0;

    // Project match
    if (memory.project === context.primary_project) {
      score += 0.35;
    } else if (context.active_projects.includes(memory.project)) {
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
   * Get recall reason
   */
  private getRecallReason(memory: any, context: ContextAnalysis): string {
    const reasons: string[] = [];

    if (memory.project === context.primary_project) {
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
}

/**
 * Factory function to create a context client
 */
export function createContextClient(options?: ContextClientOptions): ContextClient {
  return new ContextClient(options);
}
