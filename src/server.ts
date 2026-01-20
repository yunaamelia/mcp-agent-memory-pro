import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { handleStoreMemory, STORE_MEMORY_TOOL } from './tools/store.js';
import { handleSearchMemory, SEARCH_MEMORY_TOOL } from './tools/search.js';
import { handleMemoryInsights, MEMORY_INSIGHTS_TOOL } from './tools/memory_insights.js';
// Phase 3 imports
import { memoryRecallContextTool, recallContext } from './tools/memory_recall_context.js';
import { memorySuggestionsTool, getSuggestions } from './tools/memory_suggestions.js';
import { memoryAnalyticsTool, getAnalytics } from './tools/memory_analytics.js';
import { logger } from './utils/logger.js';

export async function initializeServer(server: Server) {
  logger.info('Initializing MCP server tools...');

  // Register tool list handler
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    logger.debug('Listing available tools');
    return {
      tools: [
        STORE_MEMORY_TOOL,              // Phase 1
        SEARCH_MEMORY_TOOL,             // Phase 1
        MEMORY_INSIGHTS_TOOL,           // Phase 2
        memoryRecallContextTool,        // Phase 3
        memorySuggestionsTool,          // Phase 3
        memoryAnalyticsTool,            // Phase 3
      ],
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

        case 'memory_insights': // Phase 2
          return await handleMemoryInsights(args);

        case 'memory_recall_context': { // Phase 3
          const result = await recallContext(args ?? {});
          return {
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
          };
        }

        case 'memory_suggestions': { // Phase 3
          const result = await getSuggestions(args ?? {});
          return {
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
          };
        }

        case 'memory_analytics': { // Phase 3
          const result = await getAnalytics(args ?? {});
          return {
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
          };
        }

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      logger.error(`Tool execution error for ${name}:`, error);

      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

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
