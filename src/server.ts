import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { handleStoreMemory, STORE_MEMORY_TOOL } from './tools/store.js';
import { handleSearchMemory, SEARCH_MEMORY_TOOL } from './tools/search.js';
import { logger } from './utils/logger.js';

export async function initializeServer(server: Server) {
  logger.info('Initializing MCP server tools...');

  // Register tool list handler
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    logger.debug('Listing available tools');
    return {
      tools: [STORE_MEMORY_TOOL, SEARCH_MEMORY_TOOL],
    };
  });

  // Register tool call handler
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    logger.info(`Tool called: ${name}`);
    logger.debug(`Tool arguments: `, args);

    try {
      switch (name) {
        case 'memory_store':
          return await handleStoreMemory(args);

        case 'memory_search':
          return await handleSearchMemory(args);

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      logger.error(`Tool execution error for ${name}:`, error);

      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error occurred';

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                error: errorMessage,
                tool: name,
                timestamp: new Date().toISOString(),
              },
              null,
              2
            ),
          },
        ],
        isError: true,
      };
    }
  });

  logger.info('MCP server initialized successfully');
}
