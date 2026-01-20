#!/bin/bash

echo "🚀 Phase 0 Validation Script"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Check Node.js version
echo "📦 Checking Node.js version..."
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -ge 20 ]; then
    echo -e "${GREEN}✅ Node.js v$(node -v) installed${NC}"
else
    echo -e "${RED}❌ Node.js v20+ required (found v$(node -v))${NC}"
    FAILED=1
fi

# Check Python version
echo "🐍 Checking Python version..."
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ Python $(python3 --version) installed${NC}"
else
    echo -e "${RED}❌ Python 3.10+ required${NC}"
    FAILED=1
fi

if [ $FAILED -eq 1 ]; then
    echo -e "\n${RED}Environment requirements not met. Aborting.${NC}"
    exit 1
fi

# Install Node dependencies if needed
if [ ! -d "node_modules" ]; then
    echo ""
    echo "📥 Installing Node.js dependencies..."
    npm install --silent
fi

# Run PoC tests
echo ""
echo "🧪 Running Proof of Concept Tests..."
echo "-----------------------------------"

echo ""
echo "Test 1: SQLite + FTS5"
npm run poc:sqlite
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SQLite test passed${NC}"
else
    echo -e "${RED}❌ SQLite test failed${NC}"
    FAILED=1
fi

echo ""
echo "Test 2: LanceDB"
npm run poc:lance
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ LanceDB test passed${NC}"
else
    echo -e "${RED}❌ LanceDB test failed${NC}"
    FAILED=1
fi

echo ""
echo "Test 3: TypeScript ↔ Python Bridge"
npm run poc:bridge
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Bridge test passed${NC}"
else
    echo -e "${RED}❌ Bridge test failed${NC}"
    FAILED=1
fi

echo ""
echo "=============================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All Phase 0 validations passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review the PoC code in poc/ directory"
    echo "  2. Run 'npm run poc:mcp' to test MCP server"
    echo "  3. Proceed to Phase 1 implementation"
else
    echo -e "${RED}❌ Some tests failed. Please fix before proceeding.${NC}"
    exit 1
fi
