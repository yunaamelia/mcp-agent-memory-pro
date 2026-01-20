import { config as dotenvConfig } from 'dotenv';
import { join } from 'path';
import { homedir } from 'os';
import { existsSync, mkdirSync } from 'fs';
import type { AppConfig } from '../types/config.js';

// Load environment variables
dotenvConfig();

// Determine data directory
const DEFAULT_DATA_DIR = join(homedir(), '.mcp-agent-memory');
const DATA_DIR = process.env.MCP_MEMORY_DATA_DIR || DEFAULT_DATA_DIR;

// Ensure data directory exists
if (!existsSync(DATA_DIR)) {
  mkdirSync(DATA_DIR, { recursive: true });
}

// Ensure subdirectories exist
const VECTORS_DIR = join(DATA_DIR, 'vectors');
if (!existsSync(VECTORS_DIR)) {
  mkdirSync(VECTORS_DIR, { recursive: true });
}

export const config: AppConfig = {
  // Data
  dataDir: DATA_DIR,
  databasePath: join(DATA_DIR, 'memories.db'),
  vectorStorePath: VECTORS_DIR,

  // Embedding
  embeddingServiceUrl: process.env.EMBEDDING_SERVICE_URL || 'http://127.0.0.1:5001',
  embeddingModel: process.env.EMBEDDING_MODEL || 'sentence-transformers/all-MiniLM-L6-v2',
  embeddingDimensions: parseInt(process.env.EMBEDDING_DIMENSIONS || '384', 10),

  // Memory
  shortTermDays: parseInt(process.env.SHORT_TERM_DAYS || '2', 10),
  workingTermDays: parseInt(process.env.WORKING_TERM_DAYS || '30', 10),

  // Logging
  logLevel: (process.env.LOG_LEVEL as AppConfig['logLevel']) || 'info',
  logFile: process.env.LOG_FILE || join(DATA_DIR, 'mcp-memory.log'),

  // Server
  serverName: process.env.MCP_SERVER_NAME || 'mcp-agent-memory-pro',
  serverVersion: process.env.MCP_SERVER_VERSION || '1.0.0',

  // Performance
  vectorSearchLimit: parseInt(process.env.VECTOR_SEARCH_LIMIT || '100', 10),
  cacheEnabled: process.env.CACHE_ENABLED !== 'false',
};
