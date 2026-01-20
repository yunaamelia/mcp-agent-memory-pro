import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

// Phase 1 tools
import { handleStoreMemory, STORE_MEMORY_TOOL } from './tools/store.js';
import { handleSearchMemory, SEARCH_MEMORY_TOOL } from './tools/search.js';

// Phase 2 tools
import { handleMemoryInsights, MEMORY_INSIGHTS_TOOL } from './tools/memory_insights.js';

// Phase 3 tools
import {
  recallContext,
  memoryRecallContextTool,
  memoryRecallContextSchema,
} from './tools/memory_recall_context.js';
import {
  getSuggestions,
  memorySuggestionsTool,
  memorySuggestionsSchema,
} from './tools/memory_suggestions.js';
import {
  getAnalytics,
  memoryAnalyticsTool,
  memoryAnalyticsSchema,
} from './tools/memory_analytics.js';

// Phase 4 tools
import { handleMemoryQuery, MEMORY_QUERY_TOOL } from './tools/memory_query.js';
import { handleMemoryExport, MEMORY_EXPORT_TOOL } from './tools/memory_export.js';
import { handleMemoryHealth, MEMORY_HEALTH_TOOL } from './tools/memory_health.js';
import { handleMemoryDashboard, MEMORY_DASHBOARD_TOOL } from './tools/memory_dashboard.js';

import { logger } from './utils/logger.js';

export async function initializeServer(server: Server) {
  logger.info('Initializing MCP server tools...');

  // Register tool list handler
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    logger.debug('Listing available tools');
    return {
      tools: [
        // Phase 1: Foundation (2 tools)
        STORE_MEMORY_TOOL,
        SEARCH_MEMORY_TOOL,

        // Phase 2: Intelligence (1 tool)
        MEMORY_INSIGHTS_TOOL,

        // Phase 3: Cognitive (3 tools)
        {
          name: memoryRecallContextTool.name,
          description: memoryRecallContextTool.description,
          inputSchema: memoryRecallContextTool.inputSchema,
        },
        {
          name: memorySuggestionsTool.name,
          description: memorySuggestionsTool.description,
          inputSchema: memorySuggestionsTool.inputSchema,
        },
        {
          name: memoryAnalyticsTool.name,
          description: memoryAnalyticsTool.description,
          inputSchema: memoryAnalyticsTool.inputSchema,
        },

        // Phase 4: Production (4 tools)
        MEMORY_QUERY_TOOL,
        MEMORY_EXPORT_TOOL,
        MEMORY_HEALTH_TOOL,
        MEMORY_DASHBOARD_TOOL,
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
        // Phase 1
        case 'memory_store':
          return await handleStoreMemory(args);
        case 'memory_search':
          return await handleSearchMemory(args);

        // Phase 2
        case 'memory_insights':
          return await handleMemoryInsights(args);

        // Phase 3 - These need wrappers as they return raw data
        case 'memory_recall_context': {
          const params = memoryRecallContextSchema.parse(args);
          const result = await recallContext(params);
          return {
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
          };
        }
        case 'memory_suggestions': {
          const params = memorySuggestionsSchema.parse(args);
          const result = await getSuggestions(params);
          return {
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
          };
        }
        case 'memory_analytics': {
          const params = memoryAnalyticsSchema.parse(args);
          const result = await getAnalytics(params);
          return {
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
          };
        }

        // Phase 4
        case 'memory_query':
          return await handleMemoryQuery(args);
        case 'memory_export':
          return await handleMemoryExport(args);
        case 'memory_health':
          return await handleMemoryHealth(args);
        case 'memory_dashboard':
          return await handleMemoryDashboard(args);

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
  logger.info('Total tools available:  10');
  logger.info('  Phase 1 (Foundation): 2 tools');
  logger.info('  Phase 2 (Intelligence): 1 tool');
  logger.info('  Phase 3 (Cognitive): 3 tools');
  logger.info('  Phase 4 (Production): 4 tools');
}
