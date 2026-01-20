# Configuration Guide

## Environment Variables

Create a `.env` file in the project root:

```bash
# Data Directory
MCP_MEMORY_DATA_DIR=./data

# Embedding Service
EMBEDDING_SERVICE_URL=http://127.0.0.1:5001
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384

# Memory Tiers (days)
SHORT_TERM_DAYS=2
WORKING_TERM_DAYS=30

# Logging
LOG_LEVEL=info  # debug | info | warn | error
LOG_FILE=./data/mcp-memory.log

# Server
MCP_SERVER_NAME=mcp-agent-memory-pro
MCP_SERVER_VERSION=1.0.0

# Performance
VECTOR_SEARCH_LIMIT=100
CACHE_ENABLED=true
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "agent-memory":  {
      "command": "node",
      "args": [
        "/absolute/path/to/mcp-agent-memory-pro/dist/index.js"
      ],
      "env": {
        "MCP_MEMORY_DATA_DIR": "/path/to/data",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

Windows:  `%APPDATA%\Claude\claude_desktop_config.json`

Linux: `~/.config/Claude/claude_desktop_config.json`

## Database Configuration

The system uses SQLite with WAL mode for better performance: 

- **Database Path**: `$MCP_MEMORY_DATA_DIR/memories.db`
- **Journal Mode**: WAL (Write-Ahead Logging)
- **Synchronous**:  NORMAL
- **Foreign Keys**:  Enabled

## Vector Store Configuration

LanceDB is used for vector storage: 

- **Storage Path**: `$MCP_MEMORY_DATA_DIR/vectors`
- **Format**:  Disk-based (no separate server)
- **Dimensions**: 384 (all-MiniLM-L6-v2)

## Python Service Configuration

Edit `python/config.py` for advanced settings:

```python
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
HOST = '127.0.0.1'
PORT = 5001
MAX_BATCH_SIZE = 32
WORKERS = 1
```
