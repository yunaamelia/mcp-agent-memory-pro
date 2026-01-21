/**
 * Memory Suggestions Tool
 * Generates smart suggestions based on memory patterns and context
 */

import { z } from 'zod';
import { logger } from '../utils/logger.js';
import { getDatabase } from '../storage/database.js';
import Database from 'better-sqlite3';

// Input schema for the tool
export const memorySuggestionsSchema = z.object({
  project: z.string().optional().describe('Optional project to focus suggestions on'),
  context_type: z.string().optional().describe('Type of context (coding, debugging, planning)'),
  limit: z.number().default(5).describe('Maximum suggestions to return (default: 5)'),
});

export type MemorySuggestionsInput = z.infer<typeof memorySuggestionsSchema>;

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

export interface SuggestionsResult {
  suggestions: Suggestion[];
  potential_issues: PotentialIssue[];
  forgotten_knowledge: Record<string, unknown>[];
  summary: string;
}

/**
 * Generate smart suggestions based on memory patterns
 */
export async function getSuggestions(input: MemorySuggestionsInput): Promise<SuggestionsResult> {
  const db = getDatabase();

  try {
    const suggestions: Suggestion[] = [];
    const potentialIssues: PotentialIssue[] = [];
    const forgottenKnowledge: Record<string, unknown>[] = [];

    // Get forgotten knowledge
    const forgotten = await getForgottenKnowledge(db, input.project);
    forgottenKnowledge.push(...forgotten);

    // Add forgotten knowledge as suggestions
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

    // Detect potential issues
    const issues = await detectPotentialIssues(db, input.project);
    potentialIssues.push(...issues);

    // Add high-severity issues as suggestions
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

    // Get best practice recommendations
    const practices = await getBestPractices(db, input.project);
    for (const practice of practices.slice(0, 2)) {
      suggestions.push({
        type: 'best_practice',
        title: 'Relevant past insight',
        description: practice.content || '',
        priority: 5,
        action: 'review',
        memory_id: practice.id,
        reason: 'Historical pattern',
      });
    }

    // Context-specific suggestions
    if (input.context_type === 'debugging') {
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

    // Generate summary
    const summary = generateSummary(suggestions, potentialIssues, forgottenKnowledge);

    logger.info(`Generated ${suggestions.length} suggestions`);

    return {
      suggestions: suggestions.slice(0, input.limit),
      potential_issues: potentialIssues,
      forgotten_knowledge: forgottenKnowledge,
      summary,
    };
  } catch (error) {
    logger.error('Suggestions generation failed', { error });
    throw error;
  }
}

/**
 * Get forgotten but important memories
 */
async function getForgottenKnowledge(
  db: Database.Database,
  project?: string
): Promise<
  {
    memory_id: string;
    content_preview: string;
    project: string | null;
    importance_score: number;
    days_since_access: number;
    reason: string;
  }[]
> {
  const fourteenDaysAgo = Date.now() - 14 * 24 * 60 * 60 * 1000;

  let query = `
    SELECT id, type, content, project, importance_score, last_accessed, access_count
    FROM memories
    WHERE importance_score >= 0.6
      AND (last_accessed < ? OR last_accessed IS NULL)
      AND archived = 0
  `;
  const params: (string | number)[] = [fourteenDaysAgo];

  if (project) {
    query += ' AND project = ?';
    params.push(project);
  }

  query += ' ORDER BY importance_score DESC LIMIT 10';

  const memories = db.prepare(query).all(...params) as {
    id: string;
    content: string | null;
    project: string | null;
    importance_score: number;
    last_accessed: number | null;
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
      reason: `Important memory (${m.importance_score?.toFixed(2)}) not accessed in ${daysSince} days`,
    };
  });
}

/**
 * Detect potential issues
 */
async function detectPotentialIssues(
  db: Database.Database,
  project?: string
): Promise<PotentialIssue[]> {
  const issues: PotentialIssue[] = [];

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
      if (lineLower.includes('todo') || lineLower.includes('fixme') || lineLower.includes('hack')) {
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
}

/**
 * Get best practice recommendations
 */
async function getBestPractices(
  db: Database.Database,
  project?: string
): Promise<
  {
    id: string;
    type: string;
    content: string | null;
    project: string | null;
    importance_score: number;
  }[]
> {
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

  query += ' ORDER BY importance_score DESC, timestamp DESC LIMIT 10';

  return db.prepare(query).all(...params) as {
    id: string;
    type: string;
    content: string | null;
    project: string | null;
    importance_score: number;
  }[];
}

/**
 * Generate summary
 */
function generateSummary(
  suggestions: Suggestion[],
  issues: PotentialIssue[],
  forgotten: Record<string, unknown>[]
): string {
  const parts: string[] = [];

  if (suggestions.length > 0) {
    parts.push(`${suggestions.length} suggestions available`);
  }

  const highSeverityIssues = issues.filter((i) => i.severity === 'high').length;
  if (highSeverityIssues > 0) {
    parts.push(`${highSeverityIssues} high-priority issues detected`);
  }

  if (forgotten.length > 0) {
    parts.push(`${forgotten.length} important memories need review`);
  }

  return parts.length > 0 ? parts.join('. ') + '.' : 'No suggestions at this time.';
}

// Tool definition for MCP
export const memorySuggestionsTool = {
  name: 'memory_suggestions',
  description:
    'Generates smart suggestions based on memory patterns. Returns actionable recommendations, potential issues, and forgotten knowledge that may be relevant.',
  inputSchema: memorySuggestionsSchema,
  handler: getSuggestions,
};
