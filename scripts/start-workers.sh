#!/bin/bash

# ============================================================================
# Start Background Workers
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting Background Workers${NC}"
echo ""

# Check if workers are enabled
if [ "${WORKERS_ENABLED:-true}" = "false" ]; then
    echo "Workers are disabled in configuration"
    exit 0
fi

cd "$PROJECT_ROOT"

# Ensure Python environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r python/requirements.txt
    pip install -r python/requirements-workers.txt
else
    source .venv/bin/activate
fi

# Download spaCy model if needed
echo "Checking spaCy model..."
python3 -m spacy download en_core_web_sm 2>/dev/null || true

# Start worker manager
echo -e "${GREEN}Starting worker manager...${NC}"

nohup python3 python/worker_manager.py \
    > data/worker_manager.log 2>&1 &

WORKER_PID=$!
echo $WORKER_PID > data/worker_manager.pid

echo "  ✓ Worker manager started (PID: $WORKER_PID)"
echo "  Log: data/worker_manager.log"

# Wait for workers to initialize
sleep 2

if ps -p $WORKER_PID > /dev/null; then
    echo ""
    echo -e "${GREEN}Background workers are running!${NC}"
    echo ""
    echo "Active workers:"
    echo "  • Importance Scorer (every 5 min)"
    echo "  • Entity Extractor (every 15 min)"
    echo "  • Memory Promoter (hourly)"
    echo "  • Summarizer (daily at 2 AM)"
    echo "  • Graph Builder (daily at 3 AM)"
    echo ""
    echo "Monitor: tail -f data/worker_manager.log"
    echo "Stop: ./scripts/stop-workers.sh"
else
    echo ""
    echo "⚠️  Worker manager failed to start"
    echo "Check log: cat data/worker_manager.log"
    exit 1
fi
