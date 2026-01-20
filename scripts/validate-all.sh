#!/bin/bash
# Complete System Validation
# Runs validation for all phases

set -e

cd "$(dirname "$0")/.."

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        MCP AGENT MEMORY PRO - COMPLETE VALIDATION            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

phases_passed=0
phases_failed=0

run_phase_validation() {
    local phase=$1
    local script=$2
    
    echo -e "${YELLOW}═══ Phase $phase ═══${NC}"
    
    if [ -f "$script" ]; then
        if bash "$script" 2>&1 | tail -5; then
            echo -e "${GREEN}✓ Phase $phase: PASSED${NC}"
            ((phases_passed++))
        else
            echo -e "${RED}✗ Phase $phase: FAILED${NC}"
            ((phases_failed++))
        fi
    else
        echo -e "${YELLOW}⚠ Phase $phase: Script not found ($script)${NC}"
    fi
    
    echo ""
}

# Phase 1
if [ -f "tests/validation/phase1-validate.sh" ]; then
    run_phase_validation "1" "tests/validation/phase1-validate.sh"
fi

# Phase 2
if [ -f "tests/validation/phase2-validate.sh" ]; then
    run_phase_validation "2" "tests/validation/phase2-validate.sh"
fi

# Phase 3
if [ -f "scripts/validate-phase3.sh" ]; then
    run_phase_validation "3" "scripts/validate-phase3.sh"
fi

# Phase 5 (current)
echo -e "${YELLOW}═══ Phase 5 ═══${NC}"

# Run Python tests
echo "Running Phase 5 Python tests..."
if python3 tests/phase5/test_all_phase5.py 2>&1 | tail -10; then
    echo -e "${GREEN}✓ Phase 5 Python tests: PASSED${NC}"
    ((phases_passed++))
else
    echo -e "${RED}✗ Phase 5 Python tests: FAILED${NC}"
    ((phases_failed++))
fi

# Run component validation
echo ""
echo "Running Phase 5 component validation..."
if python3 scripts/validate_phase5.py 2>&1 | tail -5; then
    echo -e "${GREEN}✓ Phase 5 components: PASSED${NC}"
    ((phases_passed++))
else
    echo -e "${RED}✗ Phase 5 components: FAILED${NC}"
    ((phases_failed++))
fi

# TypeScript build
echo ""
echo "Running TypeScript build..."
if npm run build 2>&1 | tail -3; then
    echo -e "${GREEN}✓ TypeScript build: PASSED${NC}"
    ((phases_passed++))
else
    echo -e "${RED}✗ TypeScript build: FAILED${NC}"
    ((phases_failed++))
fi

# Summary
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    VALIDATION SUMMARY                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Passed: $phases_passed"
echo "  Failed: $phases_failed"
echo ""

if [ $phases_failed -eq 0 ]; then
    echo -e "${GREEN}✅ ALL VALIDATIONS PASSED${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME VALIDATIONS FAILED${NC}"
    exit 1
fi
