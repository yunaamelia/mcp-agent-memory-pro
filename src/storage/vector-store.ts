import * as lancedb from '@lancedb/lancedb';
import { config } from '../utils/config.js';
import { logger } from '../utils/logger.js';
import { VectorStoreError } from '../utils/errors.js';

let db: lancedb.Connection | null = null;
let table: lancedb.Table | null = null;

interface VectorRecord {
  id: string;
  vector: number[];
  content: string;
  timestamp: number;
  type: string;
  tier: string;
  project?: string;
}

export async function initializeVectorStore(): Promise<void> {
  const vectorPath = config.vectorStorePath;

  logger.info(`Initializing LanceDB at: ${vectorPath}`);

  try {
    db = await lancedb.connect(vectorPath);

    // Check if table exists
    const tableNames = await db.tableNames();

    if (!tableNames.includes('memories')) {
      const sampleData: Record<string, unknown>[] = [
        {
          id: 'init',
          vector: new Array(384).fill(0.0),
          content: 'init',
          timestamp: Date.now(),
          type: 'init',
          tier: 'init',
          project: 'init',
        },
      ];
      table = await db.createTable('memories', sampleData);

      logger.info('Created LanceDB table: memories');
    } else {
      table = await db.openTable('memories');
      logger.info('Opened existing LanceDB table: memories');
    }
  } catch (error) {
    logger.error('Failed to initialize vector store:', error);
    throw new VectorStoreError('Vector store initialization failed', error as Error);
  }
}

export async function addVector(
  id: string,
  vector: number[],
  metadata: Partial<VectorRecord>
): Promise<void> {
  if (!table) {
    await initializeVectorStore();
  }

  try {
    const record: VectorRecord = {
      id,
      vector,
      content: metadata.content || '',
      timestamp: metadata.timestamp || Date.now(),
      type: metadata.type || 'note',
      tier: metadata.tier || 'short',
      project: metadata.project,
    };

    // Cast record to match generic structure required by lancedb
    await table!.add([record as unknown as Record<string, unknown>]);
    logger.debug(`Added vector for memory: ${id}`);
  } catch (error) {
    logger.error(`Failed to add vector for ${id}:`, error);
    throw new VectorStoreError(`Failed to add vector: ${id}`, error as Error);
  }
}

export async function searchVectors(
  queryVector: number[],
  limit: number = 10,
  filter?: string
): Promise<Array<VectorRecord & { _distance: number }>> {
  if (!table) {
    await initializeVectorStore();
  }

  try {
    let query = table!.search(queryVector).limit(limit);

    if (filter) {
      query = query.filter(filter);
    }

    const results = await query.toArray();

    logger.debug(`Vector search returned ${results.length} results`);

    return results as unknown as Array<VectorRecord & { _distance: number }>;
  } catch (error) {
    logger.error('Vector search failed:', error);
    throw new VectorStoreError('Vector search failed', error as Error);
  }
}

export async function deleteVector(id: string): Promise<void> {
  if (!table) {
    await initializeVectorStore();
  }

  try {
    await table!.delete(`id = '${id}'`);
    logger.debug(`Deleted vector for memory: ${id}`);
  } catch (error) {
    logger.error(`Failed to delete vector for ${id}:`, error);
    throw new VectorStoreError(`Failed to delete vector: ${id}`, error as Error);
  }
}

export function getVectorStore(): lancedb.Table {
  if (!table) {
    throw new VectorStoreError('Vector store not initialized');
  }
  return table;
}
