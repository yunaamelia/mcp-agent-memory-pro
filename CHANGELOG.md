# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-01-20

### Phase 1 - Foundation Complete

#### Added

- ✅ MCP server with stdio transport
- ✅ SQLite database with FTS5 full-text search
- ✅ LanceDB vector store integration
- ✅ Python FastAPI embedding service
- ✅ `memory_store` tool with deduplication
- ✅ `memory_search` tool with semantic search
- ✅ Rich metadata support (project, file, language, tags)
- ✅ Importance scoring
- ✅ Access count tracking
- ✅ CLI tool for testing
- ✅ Service management scripts
- ✅ Comprehensive error handling
- ✅ Logging system
- ✅ Configuration management
- ✅ Testing suite
- ✅ Complete documentation

#### Technical Details

- **Database**: SQLite 3 with WAL mode
- **Vector Store**: LanceDB disk-based
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Runtime**: Node.js 20+ and Python 3.10+

## [0.1.0] - 2026-01-19

### Phase 0 - Technical Foundation

#### Added

- ✅ Proof of concept validations
- ✅ CI/CD with GitHub Actions
- ✅ Multi-OS testing (Ubuntu, macOS, Windows)
- ✅ Development environment setup
- ✅ Automated validation scripts

---

**Next Release**: Phase 2 - Intelligence Layer (Background workers, memory promotion, entity extraction)
