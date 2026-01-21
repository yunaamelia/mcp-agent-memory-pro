#!/bin/bash
# ============================================================================
# Phase 5 Implementation Validation Script
# ============================================================================

set -e
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$SCRIPT_DIR/../phase5-validation.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

CHECK="✅"
CROSS="❌"

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}=====================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}=====================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

start_timer() {
    START_TIME=$(date +%s)
}

end_timer() {
    END_TIME=$(date +%s)
    echo $((END_TIME - START_TIME))
}

# ============================================================================
# COMPONENT TESTS
# ============================================================================

test_ml_engine() {
    echo "Testing ML engine..."
    start_timer
    
    if python3 "$PROJECT_ROOT/tests/phase5/test_ml_engine.py" >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "ML engine tests passed (${duration}s)"
        return 0
    else
        duration=$(end_timer)
        print_error "ML engine tests failed (${duration}s)"
        return 1
    fi
}

test_automation() {
    echo "Testing automation system..."
    start_timer
    
    if python3 "$PROJECT_ROOT/tests/phase5/test_automation.py" >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Automation tests passed (${duration}s)"
        return 0
    else
        duration=$(end_timer)
        print_error "Automation tests failed (${duration}s)"
        return 1
    fi
}

test_predictive() {
    echo "Testing predictive analytics..."
    start_timer
    
    if python3 "$PROJECT_ROOT/tests/phase5/test_predictive.py" >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Predictive tests passed (${duration}s)"
        return 0
    else
        duration=$(end_timer)
        print_error "Predictive tests failed (${duration}s)"
        return 1
    fi
}

test_caching() {
    echo "Testing caching system..."
    start_timer
    
    if python3 "$PROJECT_ROOT/tests/phase5/test_caching.py" >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Caching tests passed (${duration}s)"
        return 0
    else
        duration=$(end_timer)
        print_error "Caching tests failed (${duration}s)"
        return 1
    fi
}

test_plugins() {
    echo "Testing plugin system..."
    start_timer
    
    if python3 "$PROJECT_ROOT/tests/phase5/test_plugins.py" >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Plugin tests passed (${duration}s)"
        return 0
    else
        duration=$(end_timer)
        print_error "Plugin tests failed (${duration}s)"
        return 1
    fi
}

test_extensions() {
    echo "Testing extensions..."
    start_timer
    
    chmod +x "$SCRIPT_DIR/test-extensions.sh"
    if "$SCRIPT_DIR/test-extensions.sh" >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Extensions tests passed (${duration}s)"
        return 0
    else
        duration=$(end_timer)
        print_error "Extensions tests failed (${duration}s)"
        return 1
    fi
}

test_component_check() {
    echo "Running component validation..."
    start_timer
    
    if python3 "$PROJECT_ROOT/scripts/validate_phase5.py" >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Component check passed (${duration}s)"
        return 0
    else
        duration=$(end_timer)
        print_error "Component check failed (${duration}s)"
        return 1
    fi
}

test_typescript_build() {
    echo "Testing TypeScript build..."
    start_timer
    
    cd "$PROJECT_ROOT"
    if npm run build >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "TypeScript build passed (${duration}s)"
        return 0
    else
        duration=$(end_timer)
        print_error "TypeScript build failed (${duration}s)"
        return 1
    fi
}

# ============================================================================
# MAIN VALIDATION FLOW
# ============================================================================

main() {
    > "$LOG_FILE"
    
    print_header "✨ Phase 5 Advanced Intelligence & Ecosystem Validation"
    
    echo -e "${BOLD}MCP Agent Memory Pro - Complete AI Ecosystem${NC}"
    echo "Started at: $(date)"
    echo ""
    
    cd "$PROJECT_ROOT"
    
    start_timer
    TEST_FAILURES=0
    TOTAL_TESTS=0
    
    # ========================================================================
    # STEP 1: TypeScript Build
    # ========================================================================
    
    print_header "Step 1: TypeScript Build"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_typescript_build || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    # ========================================================================
    # STEP 2: ML & Automation
    # ========================================================================
    
    print_header "Step 2: ML Engine & Automation"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_ml_engine || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_automation || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    # ========================================================================
    # STEP 3: Predictive & Caching
    # ========================================================================
    
    print_header "Step 3: Predictive Analytics & Caching"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_predictive || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_caching || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    # ========================================================================
    # STEP 4: Plugin System
    # ========================================================================
    
    print_header "Step 4: Plugin System"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_plugins || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    # ========================================================================
    # STEP 5: Extensions
    # ========================================================================
    
    print_header "Step 5: Extensions (VSCode & Browser)"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_extensions || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    # ========================================================================
    # STEP 6: Component Check
    # ========================================================================
    
    print_header "Step 6: Component Validation"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_component_check || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    TOTAL_DURATION=$(end_timer)
    PASSED=$((TOTAL_TESTS - TEST_FAILURES))
    
    print_header "Validation Summary"
    
    echo "Tests: $PASSED / $TOTAL_TESTS passed"
    echo "Duration: ${TOTAL_DURATION}s"
    echo ""
    
    if [ $TEST_FAILURES -eq 0 ]; then
        echo -e "${GREEN}${BOLD}${CHECK} Phase 5 Validation PASSED!${NC}"
        echo ""
        echo "Advanced Intelligence Features:"
        echo "  ✓ ML Importance Prediction"
        echo "  ✓ Auto-Tagging with ML"
        echo "  ✓ Task Prediction"
        echo "  ✓ Smart Automation"
        echo "  ✓ Multi-level Caching"
        echo "  ✓ Plugin System"
        echo "  ✓ 3 New MCP Tools"
        echo "  ✓ VSCode Extension"
        echo "  ✓ Browser Extension"
        echo ""
        echo "Complete System:"
        echo "  • 13 MCP Tools (across 5 phases)"
        echo "  • 7 Background Workers"
        echo "  • 9 Cognitive Services"
        echo "  • 2 Extensions"
        echo "  • Plugin Architecture"
        echo ""
        exit 0
    else
        echo -e "${RED}${BOLD}${CROSS} Validation Failed${NC}"
        echo ""
        echo "$TEST_FAILURES test(s) failed"
        echo ""
        echo "Check log: $LOG_FILE"
        exit 1
    fi
}

trap 'echo -e "\n${RED}ERROR: Validation failed unexpectedly${NC}"; exit 3' ERR

main
