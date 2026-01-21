import Database from 'better-sqlite3';
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { v4 as uuidv4 } from 'uuid';
import { config } from '../utils/config.js';
import { logger } from '../utils/logger.js';
import { DatabaseError, NotFoundError } from '../utils/errors.js';
import {
  Memory,
  StoreMemoryParams,
  SearchFilters,
  MemoryType,
  MemorySource,
  MemoryTier,
} from '../types/memory.js';

interface MemoryRow {
  id: string;
  tier: string;
  type: string;
  source: string;
  content: string;
  project: string | null;
  file_path: string | null;
  language: string | null;
  tags: string | null; // JSON string
  importance: string;
  created_at: string;
  updated_at: string;
  last_accessed: string;
}

export class DatabaseManager {
  public db: Database.Database;

  constructor() {
    try {
      this.db = new Database(config.databasePath);
      this.init();
    } catch (error) {
      throw new DatabaseError('Failed to initialize database', error as Error);
    }
  }

  private init() {
    try {
      // Get the directory of the current module (works in ESM)
      const __filename = fileURLToPath(import.meta.url);
      const __dirname = dirname(__filename);

      // Schema is in the same directory as this file (storage/)
      let schemaPath = join(__dirname, 'schemas.sql');

      // Fallback: try from dist directory (compiled output)
      if (!existsSync(schemaPath)) {
        // When running from dist/, schemas.sql should be copied there or use src/
        const projectRoot = dirname(dirname(__dirname)); // Go up from dist/storage/ to project root
        schemaPath = join(projectRoot, 'src', 'storage', 'schemas.sql');
      }

      // Final fallback: try process.cwd() with src path
      if (!existsSync(schemaPath)) {
        schemaPath = join(process.cwd(), 'src', 'storage', 'schemas.sql');
      }

      logger.debug(`Loading schema from: ${schemaPath}`);
      const schema = readFileSync(schemaPath, 'utf-8');
      this.db.exec(schema);
      logger.info('Database initialized successfully');
    } catch (error) {
      throw new DatabaseError('Failed to apply database schema', error as Error);
    }
  }

  close() {
    this.db.close();
  }

  storeMemory(params: StoreMemoryParams): Memory {
    const id = uuidv4();
    const now = new Date().toISOString();

    // Default fallback if not provided, though checking params is better
    const tier = params.tier || MemoryTier.SHORT;

    const memory: MemoryRow = {
      id,
      tier,
      type: params.type,
      source: params.source,
      content: params.content,
      project: params.context?.project || null,
      file_path: params.context?.file_path || null,
      language: params.context?.language || null,
      tags: params.context?.tags ? JSON.stringify(params.context.tags) : null,
      importance: params.importance || 'medium',
      created_at: now,
      updated_at: now,
      last_accessed: now,
    };

    try {
      const stmt = this.db.prepare(`
        INSERT INTO memories (
          id, tier, type, source, content, project, file_path, language, tags, importance, created_at, updated_at, last_accessed
        ) VALUES (
          @id, @tier, @type, @source, @content, @project, @file_path, @language, @tags, @importance, @created_at, @updated_at, @last_accessed
        )
      `);

      stmt.run(memory);
      logger.debug('Stored memory', { id, tier, type: params.type });

      return this.mapRowToMemory(memory);
    } catch (error) {
      throw new DatabaseError('Failed to store memory', error as Error);
    }
  }

  getMemory(id: string): Memory {
    try {
      const stmt = this.db.prepare('SELECT * FROM memories WHERE id = ?');
      const row = stmt.get(id) as MemoryRow | undefined;

      if (!row) {
        throw new NotFoundError('Memory', id);
      }

      // Update last_accessed asynchronously (optimistic)
      this.updateLastAccessed(id);

      return this.mapRowToMemory(row);
    } catch (error) {
      if (error instanceof NotFoundError) throw error;
      throw new DatabaseError(`Failed to retrieve memory ${id}`, error as Error);
    }
  }

  private updateLastAccessed(id: string) {
    try {
      const stmt = this.db.prepare(
        'UPDATE memories SET last_accessed = CURRENT_TIMESTAMP WHERE id = ?'
      );
      stmt.run(id);
    } catch (error) {
      logger.warn(`Failed to update last_accessed for memory ${id}`, error);
    }
  }

  searchMemories(query: string, filters?: SearchFilters, limit: number = 20): Memory[] {
    try {
      // Use FTS for text search
      let sql = `
        SELECT m.*, bm.rank 
        FROM memories m
        JOIN memories_fts bm ON m.id = bm.id
        WHERE memories_fts MATCH ?
      `;

      const params: any[] = [query];

      if (filters) {
        if (filters.types && filters.types.length > 0) {
          sql += ` AND m.type IN (${filters.types.map(() => '?').join(',')})`;
          params.push(...filters.types);
        }

        if (filters.projects && filters.projects.length > 0) {
          sql += ` AND m.project IN (${filters.projects.map(() => '?').join(',')})`;
          params.push(...filters.projects);
        }

        if (filters.tiers && filters.tiers.length > 0) {
          sql += ` AND m.tier IN (${filters.tiers.map(() => '?').join(',')})`;
          params.push(...filters.tiers);
        }

        if (filters.min_importance) {
          // Skip for now
        }

        if (filters.time_range) {
          sql += ` AND m.created_at >= ? AND m.created_at <= ?`;
          params.push(filters.time_range.start.toISOString(), filters.time_range.end.toISOString());
        }
      }

      sql += ` ORDER BY bm.rank LIMIT ?`;
      params.push(limit);

      const stmt = this.db.prepare(sql);
      const rows = stmt.all(...params) as MemoryRow[];

      return rows.map(this.mapRowToMemory);
    } catch (error) {
      throw new DatabaseError('Failed to search memories', error as Error);
    }
  }

  deleteMemory(id: string): void {
    try {
      const stmt = this.db.prepare('DELETE FROM memories WHERE id = ?');
      const info = stmt.run(id);

      if (info.changes === 0) {
        throw new NotFoundError('Memory', id);
      }
      logger.info(`Deleted memory ${id}`);
    } catch (error) {
      if (error instanceof NotFoundError) throw error;
      throw new DatabaseError(`Failed to delete memory ${id}`, error as Error);
    }
  }

  private mapRowToMemory(row: MemoryRow): Memory {
    return {
      id: row.id,
      tier: row.tier as MemoryTier,
      type: row.type as MemoryType,
      source: row.source as MemorySource,
      content: row.content,
      context: {
        project: row.project || undefined,
        file_path: row.file_path || undefined,
        language: row.language || undefined,
        tags: row.tags ? JSON.parse(row.tags) : undefined,
      },
      importance: row.importance as any,
      created_at: row.created_at,
      updated_at: row.updated_at,
      last_accessed: row.last_accessed,
    };
  }
}

export const dbManager = new DatabaseManager();

export function getDatabase(): Database.Database {
  return dbManager.db;
}

export async function initializeDatabase(): Promise<void> {
  // Database is initialized in constructor of singleton instance
  // This function exists to satisfy the interface expected by consumers
  // We could add connection verification here if needed
  if (!dbManager.db.open) {
    // Re-initialize if closed?
    // Current implementation doesn't support re-opening easily as constructor did it.
    // But better-sqlite3 db object has .open boolean.
  }
}

export function closeDatabase(): void {
  dbManager.close();
}
