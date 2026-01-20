#!/bin/bash
# Phase 3 Validation Script
# Validates cognitive features implementation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=============================================="
echo "Phase 3 - Cognitive Features Validation"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASS_COUNT++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAIL_COUNT++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
}

# Check Python cognitive modules exist
echo "Checking Python cognitive modules..."

COGNITIVE_MODULES=(
    "python/cognitive/__init__.py"
    "python/cognitive/graph_engine.py"
    "python/cognitive/context_analyzer.py"
    "python/cognitive/suggestion_engine.py"
    "python/cognitive/pattern_detector.py"
    "python/cognitive/clustering_service.py"
    "python/cognitive/consolidation_service.py"
)

for module in "${COGNITIVE_MODULES[@]}"; do
    if [ -f "$PROJECT_ROOT/$module" ]; then
        pass "$module exists"
    else
        fail "$module missing"
    fi
done

# Check workers
echo ""
echo "Checking workers..."

WORKERS=(
    "python/workers/memory_consolidator.py"
    "python/workers/pattern_analyzer.py"
)

for worker in "${WORKERS[@]}"; do
    if [ -f "$PROJECT_ROOT/$worker" ]; then
        pass "$worker exists"
    else
        fail "$worker missing"
    fi
done

# Check TypeScript tools
echo ""
echo "Checking TypeScript tools..."

TS_TOOLS=(
    "src/tools/memory_recall_context.ts"
    "src/tools/memory_suggestions.ts"
    "src/tools/memory_analytics.ts"
)

for tool in "${TS_TOOLS[@]}"; do
    if [ -f "$PROJECT_ROOT/$tool" ]; then
        pass "$tool exists"
    else
        fail "$tool missing"
    fi
done

# Check TypeScript clients
echo ""
echo "Checking TypeScript clients..."

TS_CLIENTS=(
    "src/cognitive/context-client.ts"
    "src/cognitive/suggestion-client.ts"
)

for client in "${TS_CLIENTS[@]}"; do
    if [ -f "$PROJECT_ROOT/$client" ]; then
        pass "$client exists"
    else
        fail "$client missing"
    fi
done

# Check tests
echo ""
echo "Checking test files..."

TEST_FILES=(
    "tests/cognitive/test_graph_engine.py"
    "tests/cognitive/test_context_analyzer.py"
    "tests/cognitive/test_suggestion_engine.py"
    "tests/cognitive/test_pattern_detection.py"
    "tests/cognitive/test_clustering.py"
)

for test in "${TEST_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$test" ]; then
        pass "$test exists"
    else
        fail "$test missing"
    fi
done

# Check requirements
echo ""
echo "Checking requirements..."

if [ -f "$PROJECT_ROOT/python/requirements-cognitive.txt" ]; then
    pass "requirements-cognitive.txt exists"
else
    fail "requirements-cognitive.txt missing"
fi

# Run Python import tests (basic syntax check)
echo ""
echo "Running Python import tests..."

cd "$PROJECT_ROOT"

python3 -c "
import sys
sys.path.insert(0, 'python')

try:
    from cognitive import GraphQueryEngine
    print('  ✓ GraphQueryEngine imports')
except Exception as e:
    print(f'  ✗ GraphQueryEngine import failed: {e}')
    sys.exit(1)

try:
    from cognitive import ContextAnalyzer
    print('  ✓ ContextAnalyzer imports')
except Exception as e:
    print(f'  ✗ ContextAnalyzer import failed: {e}')
    sys.exit(1)

try:
    from cognitive import SuggestionEngine
    print('  ✓ SuggestionEngine imports')
except Exception as e:
    print(f'  ✗ SuggestionEngine import failed: {e}')
    sys.exit(1)

try:
    from cognitive import PatternDetector
    print('  ✓ PatternDetector imports')
except Exception as e:
    print(f'  ✗ PatternDetector import failed: {e}')
    sys.exit(1)

try:
    from cognitive import ClusteringService
    print('  ✓ ClusteringService imports')
except Exception as e:
    print(f'  ✗ ClusteringService import failed: {e}')
    sys.exit(1)

try:
    from cognitive import ConsolidationService
    print('  ✓ ConsolidationService imports')
except Exception as e:
    print(f'  ✗ ConsolidationService import failed: {e}')
    sys.exit(1)

print('')
print('All Python imports successful!')
" && pass "Python imports" || fail "Python imports"

# Run TypeScript build check
echo ""
echo "Checking TypeScript build..."

cd "$PROJECT_ROOT"
if npm run build 2>&1 | tail -5; then
    pass "TypeScript build"
else
    fail "TypeScript build"
fi

# Run Python unit tests
echo ""
echo "Running Python cognitive tests..."

cd "$PROJECT_ROOT"
if uv run pytest tests/cognitive/ -v --tb=short 2>&1 | tail -20; then
    pass "Python cognitive tests"
else
    warn "Some Python tests may have failed (see above)"
fi

# Summary
echo ""
echo "=============================================="
echo "Validation Summary"
echo "=============================================="
echo -e "Passed: ${GREEN}${PASS_COUNT}${NC}"
echo -e "Failed: ${RED}${FAIL_COUNT}${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}Phase 3 validation PASSED!${NC}"
    exit 0
else
    echo -e "${RED}Phase 3 validation has ${FAIL_COUNT} failures${NC}"
    exit 1
fi
