import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { config } from './utils/config.js';
import { logger } from './utils/logger.js';
import { handleStoreMemory, handleSearchMemory } from './tools/index.js';

export class McpMemoryServer {
  private server: Server;

  constructor() {
    this.server = new Server(
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

    this.setupHandlers();

    // Error handling
    this.server.onerror = (error) => {
      logger.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.close();
      process.exit(0);
    });
  }

  private setupHandlers() {
    this.setupToolHandlers();
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'memory_store',
          description:
            'Store a new memory (text content) with optional metadata and importance level.',
          inputSchema: {
            type: 'object',
            properties: {
              content: {
                type: 'string',
                description: 'The actual text content of the memory',
              },
              type: {
                type: 'string',
                enum: ['code', 'command', 'conversation', 'note', 'event'],
                description: 'The type of the memory (code, note, etc.)',
              },
              tier: {
                type: 'string',
                enum: ['short', 'working', 'long'],
                description: 'The memory tier (short, working, long). Defaults to short.',
              },
              source: {
                type: 'string',
                enum: ['user', 'system', 'file_change', 'conversation'],
                description: 'Origin of the memory',
              },
              importance: {
                type: 'string',
                enum: ['low', 'medium', 'high', 'critical'],
                description: 'Importance level',
              },
              context: {
                type: 'object',
                properties: {
                  project: { type: 'string' },
                  file_path: { type: 'string' },
                  language: { type: 'string' },
                  tags: { type: 'array', items: { type: 'string' } },
                },
              },
            },
            required: ['content', 'type', 'source'],
          },
        },
        {
          name: 'memory_search',
          description: 'Search for memories using semantic query and filtering.',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'The search query string',
              },
              limit: {
                type: 'number',
                description: 'Max number of results to return (default 10)',
              },
              include_related: {
                type: 'boolean',
                description: 'Whether to include related memories (graph traversal)',
              },
              filters: {
                type: 'object',
                properties: {
                  types: {
                    type: 'array',
                    items: {
                      type: 'string',
                      enum: ['code', 'command', 'conversation', 'note', 'event'],
                    },
                  },
                  tiers: {
                    type: 'array',
                    items: { type: 'string', enum: ['short', 'working', 'long'] },
                  },
                  projects: {
                    type: 'array',
                    items: { type: 'string' },
                  },
                  time_range: {
                    type: 'object',
                    properties: {
                      start: { type: 'string' },
                      end: { type: 'string' },
                    },
                  },
                },
              },
            },
            required: ['query'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      switch (request.params.name) {
        case 'memory_store':
          return handleStoreMemory(request.params.arguments);
        case 'memory_search':
          return handleSearchMemory(request.params.arguments);
        default:
          throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
      }
    });
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    logger.info('MCP Memory Server running on stdio');
  }

  async close() {
    await this.server.close();
  }
}
