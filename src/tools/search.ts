import { getDatabase } from '../storage/database.js';
import { searchVectors } from '../storage/vector-store.js';
import { embeddingClient } from '../services/embedding-client.js';
import { MemoryType, MemoryTier, SearchResult, Memory } from '../types/memory.js';
import { SearchMemorySchema } from '../utils/validators.js';
import { logger } from '../utils/logger.js';

export const SEARCH_MEMORY_TOOL = {
  name: 'memory_search',
  description:
    'Search memories using semantic similarity and optional filters. Returns relevant memories ranked by similarity score.  Supports filtering by time range, type, project, importance, and memory tier.',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Natural language search query',
      },
      filters: {
        type: 'object',
        properties: {
          time_range: {
            type: 'object',
            properties: {
              start: { type: 'string', format: 'date-time', description: 'Start timestamp' },
              end: { type: 'string', format: 'date-time', description: 'End timestamp' },
            },
            description: 'Filter by time range',
          },
          types: {
            type: 'array',
            items: {
              type: 'string',
              enum: ['code', 'command', 'conversation', 'note', 'event'],
            },
            description: 'Filter by memory types',
          },
          projects: {
            type: 'array',
            items: { type: 'string' },
            description: 'Filter by project names',
          },
          min_importance: {
            type: 'number',
            minimum: 0,
            maximum: 1,
            description: 'Minimum importance score (0-1)',
          },
          tiers: {
            type: 'array',
            items: {
              type: 'string',
              enum: ['short', 'working', 'long'],
            },
            description: 'Filter by memory tiers',
          },
        },
        description: 'Optional filters to narrow search',
      },
      limit: {
        type: 'number',
        description: 'Maximum number of results (default: 10, max: 100)',
        minimum: 1,
        maximum: 100,
      },
      include_related: {
        type: 'boolean',
        description: 'Include related memories via graph traversal (Phase 3 feature)',
      },
    },
    required: ['query'],
  },
};

export async function handleSearchMemory(args: unknown) {
  const params = SearchMemorySchema.parse(args);

  logger.info(`Searching memories: "${params.query}"`);

  // Generate query embedding
  const queryEmbedding = await embeddingClient.generateEmbedding(params.query);

  // Build LanceDB filter
  let lanceFilter: string | undefined;
  if (params.filters) {
    const conditions: string[] = [];

    if (params.filters.types && params.filters.types.length > 0) {
      const types = params.filters.types.map((t) => `'${t}'`).join(',');
      conditions.push(`type IN (${types})`);
    }

    if (params.filters.tiers && params.filters.tiers.length > 0) {
      const tiers = params.filters.tiers.map((t) => `'${t}'`).join(',');
      conditions.push(`tier IN (${tiers})`);
    }

    if (params.filters.time_range) {
      const start = new Date(params.filters.time_range.start).getTime();
      const end = new Date(params.filters.time_range.end).getTime();
      conditions.push(`timestamp >= ${start} AND timestamp <= ${end}`);
    }

    if (params.filters.projects && params.filters.projects.length > 0) {
      const projects = params.filters.projects.map((p) => `'${p}'`).join(',');
      conditions.push(`project IN (${projects})`);
    }

    if (conditions.length > 0) {
      lanceFilter = conditions.join(' AND ');
    }
  }

  // Vector search with oversampling
  const vectorResults = await searchVectors(
    queryEmbedding,
    params.limit * 2, // Get more for post-filtering
    lanceFilter
  );

  // Get full memory details from SQLite
  const db = getDatabase();
  const memoryIds = vectorResults.map((r) => r.id);

  if (memoryIds.length === 0) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              results: [],
              count: 0,
              query: params.query,
              filters: params.filters || {},
            },
            null,
            2
          ),
        },
      ],
    };
  }

  const placeholders = memoryIds.map(() => '?').join(',');
  let sqlQuery = `
    SELECT * FROM memories 
    WHERE id IN (${placeholders})
    AND archived = 0
  `;

  const sqlParams: unknown[] = [...memoryIds];

  // Apply additional SQL filters
  if (params.filters?.projects && params.filters.projects.length > 0) {
    const projectPlaceholders = params.filters.projects.map(() => '?').join(',');
    sqlQuery += ` AND project IN (${projectPlaceholders})`;
    sqlParams.push(...params.filters.projects);
  }

  if (params.filters?.min_importance !== undefined) {
    sqlQuery += ` AND importance_score >= ?`;
    sqlParams.push(params.filters.min_importance);
  }

  // Retrieve raw rows
  const rows = db.prepare(sqlQuery).all(...sqlParams) as any[];

  // Update access counts in background
  const updateStmt = db.prepare(`
    UPDATE memories 
    SET access_count = access_count + 1, last_accessed = ?  
    WHERE id = ? 
  `);

  const now = Date.now();
  for (const row of rows) {
    updateStmt.run(now, row.id);
  }

  // Update statistics
  db.prepare(
    "UPDATE statistics SET value = CAST(CAST(value AS INTEGER) + 1 AS TEXT), updated_at = ? WHERE key = 'total_searches'"
  ).run(now);

  // Combine results with similarity scores
  const results: SearchResult[] = rows.map((row) => {
    const vectorResult = vectorResults.find((v) => v.id === row.id);
    // Create nested memory object
    const memory: Memory = {
      id: row.id,
      tier: row.tier as MemoryTier,
      type: row.type as MemoryType,
      source: row.source,
      content: row.content,
      content_hash: row.content_hash,
      timestamp: row.timestamp,
      importance: row.importance || 'medium',
      importance_score: row.importance_score,
      created_at: row.created_at,
      updated_at: row.updated_at,
      access_count: row.access_count,
      last_accessed: row.last_accessed,
      archived: Boolean(row.archived),
      context: {
        project: row.project || undefined,
        file_path: row.file_path || undefined,
        language: row.language || undefined,
        tags: row.tags ? JSON.parse(row.tags) : undefined,
      },
      entities: row.entities ? JSON.parse(row.entities) : undefined,
    };

    return {
      memory: memory,
      score: vectorResult ? 1 - vectorResult._distance : 0,
      distance: vectorResult?._distance || 999,
    };
  });

  // Sort by score and limit
  results.sort((a, b) => b.score - a.score);
  const limitedResults = results.slice(0, params.limit);

  logger.info(`Found ${limitedResults.length} memories`);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          {
            results: limitedResults.map((r) => ({
              id: r.memory.id,
              type: r.memory.type,
              source: r.memory.source,
              tier: r.memory.tier,
              content:
                r.memory.content.substring(0, 500) + (r.memory.content.length > 500 ? '...' : ''),
              project: r.memory.context.project,
              file_path: r.memory.context.file_path,
              language: r.memory.context.language,
              timestamp: r.memory.timestamp
                ? new Date(r.memory.timestamp).toISOString()
                : undefined,
              importance: r.memory.importance_score,
              similarity_score: r.score.toFixed(4),
              access_count: r.memory.access_count,
              tags: r.memory.context.tags,
            })),
            count: limitedResults.length,
            query: params.query,
            filters: params.filters || {},
          },
          null,
          2
        ),
      },
    ],
  };
}
