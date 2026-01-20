#!/usr/bin/env node

import { Command } from 'commander';
import { getDatabase, initializeDatabase, closeDatabase } from './storage/database.js';
import { initializeVectorStore } from './storage/vector-store.js';
import { handleStoreMemory } from './tools/store.js';
import { handleSearchMemory } from './tools/search.js';
import { embeddingClient } from './services/embedding-client.js';
import { logger } from './utils/logger.js';
import { config } from './utils/config.js';
import { MemoryType, MemorySource } from './types/memory.js';

const program = new Command();

program
  .name('mcp-memory-cli')
  .description('CLI tool for MCP Agent Memory Pro')
  .version(config.serverVersion);

// Store command
program
  .command('store')
  .description('Store a new memory')
  .requiredOption('-c, --content <content>', 'Content to store')
  .requiredOption('-t, --type <type>', 'Memory type (code|command|conversation|note|event)')
  .option('-s, --source <source>', 'Memory source (ide|terminal|manual)', 'manual')
  .option('-p, --project <project>', 'Project name')
  .option('-f, --file <file>', 'File path')
  .option('-l, --language <language>', 'Programming language')
  .option('--tags <tags>', 'Comma-separated tags')
  .option('-i, --importance <importance>', 'Importance (low|medium|high|critical)', 'medium')
  .action(async (options) => {
    try {
      await initializeDatabase();
      await initializeVectorStore();

      await embeddingClient.waitForService(5, 1000);

      const result = await handleStoreMemory({
        content: options.content,
        type: options.type as MemoryType,
        source: options.source as MemorySource,
        context: {
          project: options.project,
          file_path: options.file,
          language: options.language,
          tags: options.tags ? options.tags.split(',') : undefined,
        },
        importance: options.importance,
      });

      console.log(result.content[0].text);
      closeDatabase();
    } catch (_error) {
      logger.error('Store command failed:', _error);
      process.exit(1);
    }
  });

// Search command
program
  .command('search')
  .description('Search memories')
  .requiredOption('-q, --query <query>', 'Search query')
  .option('-l, --limit <limit>', 'Maximum results', '10')
  .option('-t, --types <types>', 'Comma-separated memory types')
  .option('-p, --projects <projects>', 'Comma-separated project names')
  .option('--min-importance <score>', 'Minimum importance score (0-1)')
  .action(async (options) => {
    try {
      await initializeDatabase();
      await initializeVectorStore();

      await embeddingClient.waitForService(5, 1000);

      const result = await handleSearchMemory({
        query: options.query,
        limit: parseInt(options.limit, 10),
        filters: {
          types: options.types ? options.types.split(',') : undefined,
          projects: options.projects ? options.projects.split(',') : undefined,
          min_importance: options.minImportance ? parseFloat(options.minImportance) : undefined,
        },
      });

      console.log(result.content[0].text);
      closeDatabase();
    } catch (_error) {
      logger.error('Search command failed:', _error);
      process.exit(1);
    }
  });

// Stats command
program
  .command('stats')
  .description('Show memory statistics')
  .action(async () => {
    try {
      await initializeDatabase();
      const db = getDatabase();

      const stats = {
        total_memories: db
          .prepare("SELECT value FROM statistics WHERE key = 'total_memories'")
          .get() as { value: string },
        total_searches: db
          .prepare("SELECT value FROM statistics WHERE key = 'total_searches'")
          .get() as { value: string },
        by_type: db
          .prepare('SELECT type, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY type')
          .all(),
        by_tier: db
          .prepare('SELECT tier, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY tier')
          .all(),
        by_source: db
          .prepare(
            'SELECT source, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY source'
          )
          .all(),
      };

      console.log('\n📊 Memory Statistics\n');
      console.log(`Total Memories: ${stats.total_memories.value}`);
      console.log(`Total Searches: ${stats.total_searches.value}`);
      console.log('\nBy Type:');
      (stats.by_type as Array<{ type: string; count: number }>).forEach((row) => {
        console.log(`  ${row.type}: ${row.count}`);
      });
      console.log('\nBy Tier:');
      (stats.by_tier as Array<{ tier: string; count: number }>).forEach((row) => {
        console.log(`  ${row.tier}: ${row.count}`);
      });
      console.log('\nBy Source:');
      (stats.by_source as Array<{ source: string; count: number }>).forEach((row) => {
        console.log(`  ${row.source}: ${row.count}`);
      });
      console.log('');

      closeDatabase();
    } catch (_error) {
      logger.error('Stats command failed:', _error);
      process.exit(1);
    }
  });

// Health check command
program
  .command('health')
  .description('Check system health')
  .action(async () => {
    try {
      console.log('🔍 System Health Check\n');

      // Check embedding service
      console.log('Embedding Service: ');
      try {
        const health = await embeddingClient.healthCheck();
        console.log(`  ✅ Status: ${health.status}`);
        console.log(`  📦 Model: ${health.model}`);
        console.log(`  📏 Dimensions: ${health.dimensions}`);
      } catch {
        console.log('  ❌ Not available');
      }

      // Check database
      console.log('\nDatabase: ');
      try {
        await initializeDatabase();
        console.log(`  ✅ Connected:  ${config.databasePath}`);
        closeDatabase();
      } catch {
        console.log('  ❌ Connection failed');
      }

      // Check vector store
      console.log('\nVector Store:');
      try {
        await initializeVectorStore();
        console.log(`  ✅ Connected: ${config.vectorStorePath}`);
      } catch {
        console.log('  ❌ Connection failed');
      }

      console.log('');
    } catch (_error) {
      logger.error('Health check failed:', _error);
      process.exit(1);
    }
  });

program.parse();
