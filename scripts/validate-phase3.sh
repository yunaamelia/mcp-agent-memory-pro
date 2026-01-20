#!/bin/bash

# ============================================================================
# Phase 3 Validation Wrapper
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Phase 3 Validation - Cognitive AI    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Install Phase 3 dependencies
echo "Installing Phase 3 cognitive dependencies..."
cd "$PROJECT_ROOT"
uv pip install -q -r python/requirements-cognitive.txt
uv pip install networkx # Ensure networkx is present
echo "  ✓ Dependencies installed"
echo ""

# Build if needed
if [ ! -d "$PROJECT_ROOT/dist" ]; then
    echo "Building TypeScript..."
    npm run build
    echo "  ✓ Build complete"
    echo ""
fi

# Run validation
echo "Running Phase 3 validation..."
echo ""

chmod +x tests/validation/phase3-validate.sh
./tests/validation/phase3-validate.sh

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Phase 3 Validation Complete!  🎉      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
