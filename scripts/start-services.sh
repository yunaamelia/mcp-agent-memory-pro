#!/bin/bash

# ============================================================================
# Start All Services
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting MCP Agent Memory Pro Services${NC}"
echo ""

# ============================================================================
# 1. Start Python Embedding Service
# ============================================================================

echo -e "${GREEN}1. Starting Python embedding service...${NC}"

cd "$PROJECT_ROOT/python"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start service in background
nohup uvicorn embedding_service:app \
    --host 127.0.0.1 \
    --port 5001 \
    --log-level info \
    > "$PROJECT_ROOT/data/embedding-service.log" 2>&1 &

EMBEDDING_PID=$! 
echo $EMBEDDING_PID > "$PROJECT_ROOT/data/embedding-service.pid"

echo "  ✓ Embedding service started (PID: $EMBEDDING_PID)"
echo "  Log:  $PROJECT_ROOT/data/embedding-service.log"

cd "$PROJECT_ROOT"

# ============================================================================
# 2. Wait for Embedding Service
# ============================================================================

echo ""
echo -e "${GREEN}2. Waiting for embedding service to be ready...${NC}"

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://127.0.0.1:5001/health > /dev/null 2>&1; then
        echo "  ✓ Embedding service is ready"
        break
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo "  ✗ Embedding service failed to start"
        exit 1
    fi
    
    sleep 1
done

# ============================================================================
# 3. Build MCP Server
# ============================================================================

echo ""
echo -e "${GREEN}3. Building MCP server...${NC}"

npm run build

echo "  ✓ MCP server built successfully"

# ============================================================================
# Summary
# ============================================================================

echo ""
echo -e "${BLUE}All services started successfully!${NC}"
echo ""
echo "Services:"
echo "  • Embedding Service: http://127.0.0.1:5001"
echo "  • MCP Server: Ready (run 'npm start' or configure in Claude Desktop)"
echo ""
echo "To stop services:  ./scripts/stop-services.sh"
echo "To view logs: tail -f data/embedding-service. log"
echo ""
