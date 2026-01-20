# MCP Agent Memory Pro

[![Phase 0 Validation](https://github.com/ahmadrizal7/mcp-agent-memory-pro/actions/workflows/phase0-validation.yml/badge.svg)](https://github.com/ahmadrizal7/mcp-agent-memory-pro/actions/workflows/phase0-validation.yml)

> **Autonomous Agent Memory MCP Server** - Store, search, and manage agent memories with semantic understanding.

## 🌟 Features

- ✅ **Semantic Search**: Find memories by meaning, not just keywords
- ✅ **Hierarchical Memory**: Short-term, working, and long-term memory tiers
- ✅ **Rich Metadata**: Store context like project, file path, language, tags
- ✅ **Deduplication**: Automatic detection of duplicate content
- ✅ **Multiple Memory Types**: Code, commands, conversations, notes, events
- ✅ **Flexible Filtering**: Filter by type, time, project, importance
- ✅ **Local-First**: All data stored locally for privacy
- ✅ **Fast Search**: Vector similarity + SQL filters

## 📊 Status

| Component | Status |
|-----------|--------|
| Phase 0 - Foundation | ✅ Complete |
| Phase 1 - Implementation | ✅ Complete |
| Phase 2 - Intelligence | 🚧 In Progress |

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- Python 3.10+
- 500MB disk space

### Installation

```bash
# Clone repository
git clone https://github.com/ahmadrizal7/mcp-agent-memory-pro.git
cd mcp-agent-memory-pro

# Install dependencies
npm install

# Setup Python environment
cd python
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..

# Build
npm run build
```

### Start Services

```bash
# Start all services (embedding + database)
./scripts/start-services.sh
```

### Configure Claude Desktop

Add to your Claude Desktop config file:

**macOS**:  `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "agent-memory": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-agent-memory-pro/dist/index.js"]
    }
  }
}
```

Restart Claude Desktop.

## 💡 Usage

### In Claude Desktop

Once configured, Claude can use the memory system:

**Store a memory:**
> "Remember this function:  `async function fetchUser(id) { return await db.users.findById(id); }`"

**Search memories:**
> "What do you remember about fetching users from the database?"

### CLI Usage

```bash
# Store a memory
mcp-memory-cli store \
  --content "npm install installs dependencies" \
  --type note \
  --tags "npm,package-manager"

# Search memories
mcp-memory-cli search --query "how to install packages"

# View statistics
mcp-memory-cli stats

# Health check
mcp-memory-cli health
```

## 🛠️ Development

```bash
# Run tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# Lint
npm run lint

# Format
npm run format
```

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING. md)

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      MCP Client (Claude Desktop)   │
└────────────────┬────────────────────┘
                 │ stdio
                 ▼
┌─────────────────────────────────────┐
│         MCP Server (TypeScript)     │
│  ┌──────────────────────────────┐  │
│  │ Tools:  store, search         │  │
│  └──────────────────────────────┘  │
└─────────┬─────────────┬─────────────┘
          │             │
          ▼             ▼
┌──────────────┐  ┌────────────────────┐
│   SQLite     │  │   LanceDB Vectors  │
│  (Metadata)  │  │   (Embeddings)     │
└──────────────┘  └────────────────────┘
                         ▲
                         │
                ┌────────┴────────┐
                │  Python Service │
                │  (FastAPI)      │
                │  Embeddings     │
                └─────────────────┘
```

## 🔧 Scripts

```bash
npm start              # Start MCP server
npm run start:python   # Start embedding service
npm run start:all      # Start all services
./scripts/stop-services.sh   # Stop all services
./scripts/reset-data.sh      # Reset all data
```

## 📈 Roadmap

- [x] Phase 0: Technical validation
- [x] Phase 1: Foundation implementation
- [ ] Phase 2: Intelligence layer (background workers)
- [ ] Phase 3:  Cognitive features (graph, insights)
- [ ] Phase 4: Analytics and patterns

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details. 

## 👤 Author

**ahmadrizal7**

---

**Built with:**  TypeScript · Python · SQLite · LanceDB · FastAPI · MCP SDK
