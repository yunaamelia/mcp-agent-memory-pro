#!/bin/bash

# ============================================================================
# Reset All Data
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}WARNING: This will delete all stored memories! ${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no) " -r
echo

if [[ !  $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo -e "${YELLOW}Resetting data...${NC}"
echo ""

# Stop services first
"$SCRIPT_DIR/stop-services.sh"

# Remove database
if [ -f "$PROJECT_ROOT/data/memories.db" ]; then
    rm "$PROJECT_ROOT/data/memories.db"
    rm -f "$PROJECT_ROOT/data/memories.db-shm"
    rm -f "$PROJECT_ROOT/data/memories.db-wal"
    echo "  ✓ Removed database"
fi

# Remove vector store
if [ -d "$PROJECT_ROOT/data/vectors" ]; then
    rm -rf "$PROJECT_ROOT/data/vectors"
    mkdir -p "$PROJECT_ROOT/data/vectors"
    echo "  ✓ Removed vector store"
fi

# Remove logs
if [ -f "$PROJECT_ROOT/data/mcp-memory. log" ]; then
    rm "$PROJECT_ROOT/data/mcp-memory.log"
    echo "  ✓ Removed logs"
fi

if [ -f "$PROJECT_ROOT/data/embedding-service.log" ]; then
    rm "$PROJECT_ROOT/data/embedding-service.log"
    echo "  ✓ Removed embedding service logs"
fi

echo ""
echo "Data reset complete.  Run './scripts/start-services.sh' to restart."
echo ""
