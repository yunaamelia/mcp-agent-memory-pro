#!/usr/bin/env node
/**
 * Proof of Concept: MCP Server responds to tool calls
 * Validates: @modelcontextprotocol/sdk works with TypeScript + Node.js
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const server = new McpServer({
    name: 'poc-mcp-server',
    version: '0.0.1',
});

// Register echo tool
server.tool(
    'echo',
    'Echo back the input message',
    {
        message: z.string().describe('Message to echo'),
    },
    async ({ message }) => {
        return {
            content: [
                {
                    type: 'text',
                    text: `Echo: ${message}`,
                },
            ],
        };
    }
);

// Register get-time tool
server.tool(
    'get-time',
    'Returns the current timestamp',
    {},
    async () => {
        const now = new Date();
        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        timestamp: now.toISOString(),
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    }),
                },
            ],
        };
    }
);

async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('✅ MCP Hello World server running...');
}

main().catch(console.error);
