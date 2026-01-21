/**
 * Suggestion Client
 * TypeScript client for suggestion and recommendation services
 */

import { logger } from '../utils/logger.js';
import { getDatabase } from '../storage/database.js';
import { ContextClient } from './context-client.js';

export interface Suggestion {
  type: string;
  title: string;
  description: string;
  priority: number;
  action: string;
  memory_id?: string;
  reason?: string;
}

export interface PotentialIssue {
  type: string;
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  memory_id?: string;
}

export interface ForgottenKnowledge {
  memory_id: string;
  content_preview: string;
  project: string | null;
  importance_score: number;
  days_since_access: number;
  reason: string;
}

export interface SuggestionClientOptions {
  forgottenThresholdDays?: number;
  suggestionLimit?: number;
}

/**
 * Client for suggestion and recommendation operations
 */
export class SuggestionClient {
  private forgottenThresholdDays: number;
  private suggestionLimit: number;
  private contextClient: ContextClient;

  constructor(options: SuggestionClientOptions = {}) {
    this.forgottenThresholdDays = options.forgottenThresholdDays ?? 14;
    this.suggestionLimit = options.suggestionLimit ?? 5;
    this.contextClient = new ContextClient();
  }

  /**
   * Get all suggestions based on current context
   */
  async getSuggestions(project?: string, contextType?: string): Promise<Suggestion[]> {
    const suggestions: Suggestion[] = [];

    try {
      // Get context
      const context = await this.contextClient.analyzeContext(project);

      // Add forgotten knowledge suggestions
      const forgotten = await this.getForgottenKnowledge(project);
      for (const item of forgotten.slice(0, 2)) {
        suggestions.push({
          type: 'forgotten_knowledge',
          title: 'Review forgotten important memory',
          description: item.content_preview,
          priority: 7,
          action: 'review',
          memory_id: item.memory_id,
          reason: item.reason,
        });
      }

      // Add issue suggestions
      const issues = await this.getPotentialIssues(project);
      for (const issue of issues.filter((i) => i.severity === 'high').slice(0, 2)) {
        suggestions.push({
          type: 'issue_suggestion',
          title: issue.title,
          description: issue.description,
          priority: 9,
          action: 'investigate',
          memory_id: issue.memory_id,
          reason: 'Potential issue detected',
        });
      }

      // Context-specific suggestions
      const effectiveContextType = contextType || context.context_type;
      if (effectiveContextType === 'debugging') {
        suggestions.push({
          type: 'pattern_suggestion',
          title: 'Check error patterns',
          description: 'You appear to be debugging. Consider checking past error resolutions.',
          priority: 8,
          action: 'search_errors',
          reason: 'Debugging context detected',
        });
      }

      // Sort by priority
      suggestions.sort((a, b) => b.priority - a.priority);

      return suggestions.slice(0, this.suggestionLimit);
    } catch (error) {
      logger.error('Get suggestions failed', { error });
      throw error;
    }
  }

  /**
   * Get forgotten but important memories
   */
  async getForgottenKnowledge(project?: string): Promise<ForgottenKnowledge[]> {
    const db = getDatabase();
    const thresholdTime = Date.now() - this.forgottenThresholdDays * 24 * 60 * 60 * 1000;

    try {
      let query = `
        SELECT id, type, content, project, importance_score, last_accessed, access_count
        FROM memories
        WHERE importance_score >= 0.6
          AND (last_accessed < ? OR last_accessed IS NULL)
          AND archived = 0
      `;
      const params: (string | number)[] = [thresholdTime];

      if (project) {
        query += ' AND project = ?';
        params.push(project);
      }

      query += ' ORDER BY importance_score DESC LIMIT 10';

      const memories = db.prepare(query).all(...params) as {
        id: string;
        type: string;
        content: string | null;
        project: string | null;
        importance_score: number;
        last_accessed: number | null;
        access_count: number;
      }[];

      return memories.map((m) => {
        const daysSince = m.last_accessed
          ? Math.floor((Date.now() - m.last_accessed) / (24 * 60 * 60 * 1000))
          : 999;

        return {
          memory_id: m.id,
          content_preview: (m.content || '').slice(0, 200),
          project: m.project,
          importance_score: m.importance_score,
          days_since_access: daysSince,
          reason: `Important memory (${(m.importance_score || 0).toFixed(2)}) not accessed in ${daysSince} days`,
        };
      });
    } catch (error) {
      logger.error('Get forgotten knowledge failed', { error });
      throw error;
    }
  }

  /**
   * Detect potential issues
   */
  async getPotentialIssues(project?: string): Promise<PotentialIssue[]> {
    const db = getDatabase();
    const issues: PotentialIssue[] = [];

    try {
      // Find unresolved TODOs
      let todoQuery = `
        SELECT id, content, project
        FROM memories
        WHERE (content LIKE '%TODO%' OR content LIKE '%FIXME%' OR content LIKE '%HACK%')
          AND archived = 0
      `;
      const todoParams: (string | number)[] = [];

      if (project) {
        todoQuery += ' AND project = ?';
        todoParams.push(project);
      }

      todoQuery += ' ORDER BY timestamp DESC LIMIT 10';

      const todos = db.prepare(todoQuery).all(...todoParams) as {
        id: string;
        content: string | null;
        project: string | null;
      }[];

      for (const todo of todos) {
        const content = todo.content || '';
        const lines = content.split('\n');

        for (const line of lines) {
          const lineLower = line.toLowerCase();
          if (
            lineLower.includes('todo') ||
            lineLower.includes('fixme') ||
            lineLower.includes('hack')
          ) {
            issues.push({
              type: 'unresolved_todo',
              title: 'Unresolved TODO',
              description: line.trim().slice(0, 100),
              severity: 'medium',
              memory_id: todo.id,
            });
            break;
          }
        }
      }

      // Find repeated errors
      const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;

      let errorQuery = `
        SELECT content_hash, content, COUNT(*) as count
        FROM memories
        WHERE (content LIKE '%error%' OR content LIKE '%Error%' OR content LIKE '%exception%')
          AND timestamp > ?
          AND archived = 0
      `;
      const errorParams: (string | number)[] = [weekAgo];

      if (project) {
        errorQuery += ' AND project = ?';
        errorParams.push(project);
      }

      errorQuery += ' GROUP BY content_hash HAVING count > 1 LIMIT 5';

      const errors = db.prepare(errorQuery).all(...errorParams) as {
        content_hash: string;
        content: string | null;
        count: number;
      }[];

      for (const error of errors) {
        issues.push({
          type: 'repeated_error',
          title: `Repeated error (${error.count} times)`,
          description: (error.content || '').slice(0, 100) + '...',
          severity: error.count >= 3 ? 'high' : 'medium',
        });
      }

      return issues.slice(0, 5);
    } catch (error) {
      logger.error('Get potential issues failed', { error });
      throw error;
    }
  }

  /**
   * Get best practice recommendations
   */
  async getBestPractices(
    project?: string,
    limit: number = 5
  ): Promise<
    {
      id: string;
      type: string;
      content: string | null;
      project: string | null;
      importance_score: number;
    }[]
  > {
    const db = getDatabase();

    try {
      let query = `
        SELECT id, type, content, project, importance_score
        FROM memories
        WHERE type IN ('decision', 'insight', 'note')
          AND importance_score >= 0.7
          AND archived = 0
      `;
      const params: (string | number)[] = [];

      if (project) {
        query += ' AND project = ?';
        params.push(project);
      }

      query += ' ORDER BY importance_score DESC, timestamp DESC LIMIT ?';
      params.push(limit);

      return db.prepare(query).all(...params) as {
        id: string;
        type: string;
        content: string | null;
        project: string | null;
        importance_score: number;
      }[];
    } catch (error) {
      logger.error('Get best practices failed', { error });
      throw error;
    }
  }
}

/**
 * Factory function to create a suggestion client
 */
export function createSuggestionClient(options?: SuggestionClientOptions): SuggestionClient {
  return new SuggestionClient(options);
}
