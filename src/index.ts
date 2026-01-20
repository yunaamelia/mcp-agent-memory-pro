#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { initializeServer } from './server.js';
import { initializeDatabase, closeDatabase } from './storage/database.js';
import { initializeVectorStore } from './storage/vector-store.js';
import { embeddingClient } from './services/embedding-client.js';
import { logger } from './utils/logger.js';
import { config } from './utils/config.js';

async function main() {
  try {
    logger.info('='.repeat(60));
    logger.info(`Starting ${config.serverName} v${config.serverVersion}`);
    logger.info('='.repeat(60));

    // Check embedding service availability
    logger.info('Checking embedding service availability...');
    try {
      await embeddingClient.waitForService(10, 1000);
    } catch (error) {
      logger.error('Embedding service is not available');
      logger.error('Please start the embedding service first: ');
      logger.error('  cd python && source venv/bin/activate && uvicorn embedding_service:app --host 127.0.0.1 --port 5001');
      process.exit(1);
    }

    // Initialize database
    logger.info('Initializing database...');
    await initializeDatabase();

    // Initialize vector store
    logger.info('Initializing vector store...');
    await initializeVectorStore();

    // Create MCP server
    const server = new Server(
      {
        name: config.serverName,
        version: config.serverVersion,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Initialize tools and handlers
    await initializeServer(server);

    // Connect using stdio transport
    const transport = new StdioServerTransport();
    await server.connect(transport);

    logger.info('='.repeat(60));
    logger.info('MCP Agent Memory Pro server is running');
    logger.info('Waiting for requests via stdio...');
    logger.info('='.repeat(60));
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGINT', () => {
  logger.info('Received SIGINT, shutting down gracefully...');
  closeDatabase();
  process.exit(0);
});

process.on('SIGTERM', () => {
  logger.info('Received SIGTERM, shutting down gracefully...');
  closeDatabase();
  process.exit(0);
});

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  logger.error('Uncaught exception:', error);
  closeDatabase();
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  logger.error('Unhandled rejection:', reason);
  closeDatabase();
  process.exit(1);
});

main();
