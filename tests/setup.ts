import { join } from 'path';
import { jest } from '@jest/globals';

// Use separate test database
process.env.MCP_MEMORY_DATA_DIR = join(process.cwd(), 'tests/data');
process.env.LOG_LEVEL = 'error';

// Mock embedding service for tests
global.fetch = jest.fn() as unknown as typeof fetch;
