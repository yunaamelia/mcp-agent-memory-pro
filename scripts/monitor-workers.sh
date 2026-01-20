#!/bin/bash

# ============================================================================
# Monitor Worker Health
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Worker Health Monitor"
echo "===================="
echo ""

# Check if worker manager is running
if [ -f "$PROJECT_ROOT/data/worker_manager.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/data/worker_manager.pid")
    
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Worker Manager: Running (PID: $PID)"
        
        # Check memory usage
        MEM=$(ps -o rss= -p $PID | awk '{print $1/1024}')
        echo "  Memory: ${MEM} MB"
        
        # Check uptime
        START_TIME=$(ps -o lstart= -p $PID)
        echo "  Started: $START_TIME"
    else
        echo -e "${RED}✗${NC} Worker Manager: Not running (stale PID file)"
    fi
else
    echo -e "${RED}✗${NC} Worker Manager: Not running"
fi

echo ""
echo "Recent Worker Activity:"
echo "----------------------"

# Show last 10 lines from worker logs
for worker_log in "$PROJECT_ROOT/data/worker_logs"/*.log; do
    if [ -f "$worker_log" ]; then
        worker_name=$(basename "$worker_log" .log)
        echo ""
        echo "$worker_name:"
        tail -n 3 "$worker_log" | sed 's/^/  /'
    fi
done

echo ""
echo "Main Log:"
tail -n 5 "$PROJECT_ROOT/data/worker_manager.log" 2>/dev/null | sed 's/^/  /' || echo "  No log file"

echo ""
