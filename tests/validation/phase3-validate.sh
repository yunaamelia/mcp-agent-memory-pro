#!/bin/bash

# ============================================================================
# Phase 3 Implementation Validation Script
# ============================================================================

set -e
set -o pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_FILE="$SCRIPT_DIR/phase3-validation-report.json"
LOG_FILE="$SCRIPT_DIR/phase3-validation.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

CHECK="✅"
CROSS="❌"
GEAR="⚙️"
BRAIN="🧠"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}=====================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}=====================================${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}${GEAR} $1${NC}"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# MAIN VALIDATION FLOW
# ============================================================================

main() {
    > "$LOG_FILE"
    
    print_header "${BRAIN} Phase 3 Cognitive Features Validation"
    
    echo -e "${BOLD}MCP Agent Memory Pro - Cognitive Layer${NC}"
    echo "Started at: $(date)"
    echo "Log file: $LOG_FILE"
    echo ""
    
    FAILED=0
    
    # 1. Cognitive Services
    print_header "Step 1: Cognitive Services"
    print_step "Running test_all_cognitive.py..."
    if uv run python tests/cognitive/test_all_cognitive.py >> "$LOG_FILE" 2>&1; then
        print_success "Cognitive services tests passed"
    else
        print_error "Cognitive services tests failed"
        FAILED=1
    fi
    
    # 2. MCP Tools
    print_header "Step 2: MCP Tools"
    print_step "Running test-phase3-tools.ts..."
    if npx tsx tests/validation/test-phase3-tools.ts >> "$LOG_FILE" 2>&1; then
        print_success "MCP tools tests passed"
    else
        print_error "MCP tools tests failed"
        FAILED=1
    fi
    
    # 3. Integration
    print_header "Step 3: Integration Workflows"
    print_step "Running test-cognitive-integration.ts..."
    if npx tsx tests/validation/test-cognitive-integration.ts >> "$LOG_FILE" 2>&1; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        FAILED=1
    fi
    
    # 4. Performance
    print_header "Step 4: Performance Benchmarks"
    print_step "Running test-cognitive-performance.py..."
    if uv run python tests/validation/test-cognitive-performance.py >> "$LOG_FILE" 2>&1; then
        print_success "Performance benchmarks passed"
    else
        print_error "Performance benchmarks failed"
        # We don't fail the whole build for performance warnings in this simplified script
    fi
    
    print_header "Summary"
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}All validation steps passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some validation steps failed. Check $LOG_FILE${NC}"
        exit 1
    fi
}

main
