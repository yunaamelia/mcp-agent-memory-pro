#!/bin/bash

# ============================================================================
# Stop All Services
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}Stopping MCP Agent Memory Pro Services${NC}"
echo ""

# Stop embedding service
if [ -f "$PROJECT_ROOT/data/embedding-service.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/data/embedding-service.pid")
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "  ✓ Stopped embedding service (PID: $PID)"
        rm "$PROJECT_ROOT/data/embedding-service.pid"
    else
        echo "  ⚠ Embedding service not running"
        rm "$PROJECT_ROOT/data/embedding-service.pid"
    fi
else
    echo "  ⚠ No PID file found for embedding service"
fi

# Cleanup any orphaned processes
pkill -f "uvicorn embedding_service:app" 2>/dev/null && echo "  ✓ Cleaned up orphaned processes"

echo ""
echo -e "${GREEN}All services stopped${NC}"
echo ""
