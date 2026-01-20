#!/bin/bash
# Phase 5 Validation Script
# Runs all Phase 5 validation tests

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           PHASE 5 VALIDATION - FULL SUITE                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")/../.."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

run_test() {
    local name=$1
    local cmd=$2
    
    echo -n "Testing $name... "
    
    if eval "$cmd" > /tmp/phase5_test_output.txt 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((failed++))
        cat /tmp/phase5_test_output.txt
    fi
}

# 1. Python Tests
echo ""
echo "═══ Python Tests ═══"

run_test "ML Engine" "python3 tests/phase5/test_ml_engine.py"
run_test "Automation" "python3 tests/phase5/test_automation.py"
run_test "Predictive" "python3 tests/phase5/test_predictive.py"
run_test "Caching" "python3 tests/phase5/test_caching.py"
run_test "Plugins" "python3 tests/phase5/test_plugins.py"

# 2. Plugin & Caching pytest
echo ""
echo "═══ Pytest Tests ═══"

run_test "Pytest Suite" "pytest tests/phase5/test_plugins_caching.py -v"

# 3. TypeScript Build
echo ""
echo "═══ TypeScript Validation ═══"

run_test "TypeScript Build" "npm run build"

# 4. Existing Validation
echo ""
echo "═══ Phase 5 Component Check ═══"

run_test "Component Check" "python3 scripts/validate_phase5.py"

# 5. Extensions Check
echo ""
echo "═══ Extension Files ═══"

if [ -f "extensions/vscode/package.json" ] && [ -f "extensions/browser/manifest.json" ]; then
    echo -e "${GREEN}✓ Extension files exist${NC}"
    ((passed++))
else
    echo -e "${RED}✗ Missing extension files${NC}"
    ((failed++))
fi

# Summary
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    VALIDATION SUMMARY                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Passed: $passed"
echo "  Failed: $failed"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ PHASE 5 VALIDATION SUCCESSFUL${NC}"
    exit 0
else
    echo -e "${RED}❌ PHASE 5 VALIDATION FAILED${NC}"
    exit 1
fi
