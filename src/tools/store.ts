import { randomUUID } from 'crypto';
import { createHash } from 'crypto';
import { getDatabase } from '../storage/database.js';
import { addVector } from '../storage/vector-store.js';
import { embeddingClient } from '../services/embedding-client.js';
import { MemoryTier } from '../types/memory.js';
import { StoreMemorySchema } from '../utils/validators.js';
import { logger } from '../utils/logger.js';

export const STORE_MEMORY_TOOL = {
  name: 'memory_store',
  description:
    'Store a new memory (code snippet, command, note, conversation, or event) in the agent memory system.  The memory will be indexed for semantic search and associated with metadata for filtering.',
  inputSchema: {
    type: 'object',
    properties: {
      content: {
        type: 'string',
        description: 'The content to store (code, command, note, etc.)',
      },
      type: {
        type: 'string',
        enum: ['code', 'command', 'conversation', 'note', 'event'],
        description: 'Type of memory being stored',
      },
      source: {
        type: 'string',
        enum: ['ide', 'terminal', 'manual'],
        description: 'Source of the memory',
      },
      context: {
        type: 'object',
        properties: {
          project: { type: 'string', description: 'Project or repository name' },
          file_path: { type: 'string', description: 'File path (for code)' },
          language: { type: 'string', description: 'Programming language (for code)' },
          tags: {
            type: 'array',
            items: { type: 'string' },
            description: 'Custom tags for categorization',
          },
        },
        description: 'Optional context information',
      },
      importance: {
        type: 'string',
        enum: ['low', 'medium', 'high', 'critical'],
        description: 'Importance level (default: medium)',
      },
    },
    required: ['content', 'type', 'source'],
  },
};

const IMPORTANCE_SCORES: Record<string, number> = {
  low: 0.25,
  medium: 0.5,
  high: 0.75,
  critical: 1.0,
};

export async function handleStoreMemory(args: unknown) {
  const params = StoreMemorySchema.parse(args);

  const db = getDatabase();
  const id = randomUUID();
  const timestamp = Date.now();

  // Generate content hash for deduplication
  const contentHash = createHash('sha256').update(params.content).digest('hex');

  // Check for duplicates
  const existing = db
    .prepare('SELECT id FROM memories WHERE content_hash = ?  AND archived = 0')
    .get(contentHash) as { id: string } | undefined;

  if (existing) {
    logger.info(`Duplicate memory detected:  ${contentHash}`);
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              success: false,
              error: 'Duplicate memory',
              existing_memory_id: existing.id,
              message: 'This content has already been stored',
            },
            null,
            2
          ),
        },
      ],
    };
  }

  // Calculate importance score
  const importanceScore = IMPORTANCE_SCORES[params.importance || 'medium'];

  // Generate embedding
  logger.info(`Generating embedding for memory: ${id}`);
  const embedding = await embeddingClient.generateEmbedding(params.content);

  // Store in SQLite
  const stmt = db.prepare(`
    INSERT INTO memories (
      id, tier, type, source, content, content_hash,
      timestamp, project, file_path, language, tags,
      importance_score, created_at, last_accessed
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  stmt.run(
    id,
    MemoryTier.SHORT,
    params.type,
    params.source,
    params.content,
    contentHash,
    timestamp,
    params.context?.project || null,
    params.context?.file_path || null,
    params.context?.language || null,
    params.context?.tags ? JSON.stringify(params.context.tags) : null,
    importanceScore,
    timestamp,
    timestamp
  );

  // Store vector embedding
  await addVector(id, embedding, {
    content: params.content,
    timestamp,
    type: params.type,
    tier: MemoryTier.SHORT,
    project: params.context?.project,
  });

  // Update statistics
  db.prepare(
    "UPDATE statistics SET value = CAST(CAST(value AS INTEGER) + 1 AS TEXT), updated_at = ? WHERE key = 'total_memories'"
  ).run(timestamp);

  logger.info(`Memory stored successfully: ${id}`);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          {
            success: true,
            memory_id: id,
            type: params.type,
            source: params.source,
            importance: params.importance || 'medium',
            timestamp: new Date(timestamp).toISOString(),
            context: params.context || {},
          },
          null,
          2
        ),
      },
    ],
  };
}
