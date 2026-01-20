#!/bin/bash

# ============================================================================
# Stop Background Workers
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}Stopping Background Workers${NC}"
echo ""

# Stop worker manager
if [ -f "$PROJECT_ROOT/data/worker_manager.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/data/worker_manager.pid")
    
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "  ✓ Stopped worker manager (PID: $PID)"
        rm "$PROJECT_ROOT/data/worker_manager.pid"
    else
        echo "  ⚠  Worker manager not running"
        rm "$PROJECT_ROOT/data/worker_manager.pid"
    fi
else
    echo "  ⚠  No PID file found"
fi

# Cleanup any orphaned processes
pkill -f "worker_manager.py" 2>/dev/null && echo "  ✓ Cleaned up orphaned processes"

echo ""
echo -e "${GREEN}Workers stopped${NC}"
