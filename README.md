# MCP Agent Memory Pro

[![Phase 0 Validation](https://github.com/ahmadrizal7/mcp-agent-memory-pro/actions/workflows/phase0-validation.yml/badge.svg)](https://github.com/ahmadrizal7/mcp-agent-memory-pro/actions/workflows/phase0-validation.yml)
[![Nightly Build](https://github.com/ahmadrizal7/mcp-agent-memory-pro/actions/workflows/phase0-nightly.yml/badge.svg)](https://github.com/ahmadrizal7/mcp-agent-memory-pro/actions/workflows/phase0-nightly.yml)

> **Status:** ✅ Phase 0 Complete | 🏗️ Phase 1 - Foundation Implementation

Intelligent memory management for AI agents using Model Context Protocol (MCP).

## Technology Stack

| Component | Technology | Status |
|-----------|-----------|--------|
| **MCP Server** | `@modelcontextprotocol/sdk` | 🔄 Validating |
| **Metadata Storage** | SQLite + FTS5 | 🔄 Validating |
| **Vector Storage** | LanceDB | 🔄 Validating |
| **Embeddings** | Sentence Transformers | 🔄 Validating |
| **Runtime** | Node.js 20 + Python 3.11 | ✅ Ready |

## Quick Start

### Prerequisites

- Node.js v20+
- Python 3.10+
- Git

### Installation

```bash
# Install Node.js dependencies
npm install

# Setup Python environment (optional, for embedding tests)
cd poc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

### Run Validation

```bash
# Run all PoC tests
./poc/validate-all.sh

# Or run individually
npm run poc:sqlite      # SQLite + FTS5
npm run poc:lance       # LanceDB vectors
npm run poc:bridge      # TypeScript ↔ Python
npm run poc:mcp         # MCP Hello World
```

## Project Structure

```
mcp-agent-memory-pro/
├── poc/                      # Proof of Concept tests
│   ├── 01-mcp-hello.ts       # MCP server basics
│   ├── 02-sqlite-test.ts     # SQLite + FTS5
│   ├── 03-lancedb-test.ts    # Vector storage
│   ├── 04-embedding-test.py  # Sentence Transformers
│   ├── 05-python-bridge-test.ts  # HTTP communication
│   ├── requirements.txt      # Python dependencies
│   └── validate-all.sh       # Validation runner
├── src/                      # Source code (Phase 1+)
├── package.json
├── tsconfig.json
└── README.md
```

## Development

```bash
# Lint code
npm run lint

# Format code
npm run format

# Type check
npm run typecheck
```

## Troubleshooting

### LanceDB installation fails
```bash
# May need build tools on Linux
sudo apt-get install -y python3-dev build-essential
```

### Python version issues
```bash
# Use pyenv
pyenv install 3.11
pyenv local 3.11
```

---

**Phase 0 Timeline:** 3-5 days  
**Next:** Phase 1 - Foundation Implementation
