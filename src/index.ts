import { McpMemoryServer } from './server.js';
import { logger } from './utils/logger.js';

async function main() {
  try {
    const server = new McpMemoryServer();
    await server.start();
  } catch (error) {
    logger.error('Fatal error starting server', error);
    process.exit(1);
  }
}

main();
