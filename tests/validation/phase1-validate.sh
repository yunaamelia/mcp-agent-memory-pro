#!/bin/bash

# ============================================================================
# Phase 1 Implementation Validation Script
# ============================================================================
# Purpose: Comprehensive validation of Phase 1 implementation
# Tests: 
#   1. Database operations (SQLite + FTS5)
#   2. Vector store operations (LanceDB)
#   3. Embedding service integration
#   4. MCP tool functionality
#   5. End-to-end workflows
#   6. Performance benchmarks
# ============================================================================

set -e
set -o pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_FILE="$SCRIPT_DIR/../validation-report.json"
LOG_FILE="$SCRIPT_DIR/../validation.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Emojis
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
ROCKET="🚀"
CLOCK="⏱️"
CHART="📊"
GEAR="⚙️"

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

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

start_timer() {
    START_TIME=$(date +%s)
}

end_timer() {
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo $DURATION
}

# Initialize report
init_report() {
    cat > "$REPORT_FILE" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "phase": "Phase 1 - Implementation",
  "environment": {
    "node_version": "$(node -v)",
    "python_version": "$(python3 --version 2>&1)",
    "os": "$(uname -s)"
  },
  "components": [],
  "integration_tests": [],
  "performance":  {},
  "summary": {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0
  },
  "duration_seconds": 0,
  "status": "running"
}
EOF
}

update_report() {
    local component=$1
    local test_name=$2
    local status=$3
    local duration=$4
    local details=$5
    
    python3 <<EOF
import json

with open('$REPORT_FILE', 'r') as f:
    report = json.load(f)

# Find or create component
component_found = False
for comp in report['components']:
    if comp['name'] == '$component':
        comp['tests'].append({
            'name':  '$test_name',
            'status': '$status',
            'duration_seconds': $duration,
            'details': '$details'
        })
        component_found = True
        break

if not component_found:
    report['components'].append({
        'name': '$component',
        'tests': [{
            'name': '$test_name',
            'status': '$status',
            'duration_seconds': $duration,
            'details': '$details'
        }]
    })

# Update summary
report['summary']['total_tests'] += 1
if '$status' == 'passed': 
    report['summary']['passed'] += 1
elif '$status' == 'failed': 
    report['summary']['failed'] += 1
else:
    report['summary']['warnings'] += 1

with open('$REPORT_FILE', 'w') as f:
    json.dump(report, f, indent=2)
EOF
}

finalize_report() {
    local total_duration=$1
    local final_status=$2
    
    python3 <<EOF
import json

with open('$REPORT_FILE', 'r') as f:
    report = json.load(f)

report['duration_seconds'] = $total_duration
report['status'] = '$final_status'

with open('$REPORT_FILE', 'w') as f:
    json.dump(report, f, indent=2)
EOF
}

# ============================================================================
# PREREQUISITE CHECKS
# ============================================================================

check_build() {
    print_step "Checking if project is built..."
    
    if [ ! -d "$PROJECT_ROOT/dist" ]; then
        print_error "Project not built. Running build..."
        cd "$PROJECT_ROOT"
        npm run build
        if [ $?  -eq 0 ]; then
            print_success "Build completed"
            return 0
        else
            print_error "Build failed"
            return 1
        fi
    else
        print_success "Project is built"
        return 0
    fi
}

check_services() {
    print_step "Checking if services are running..."
    
    # Check embedding service
    if curl -s http://127.0.0.1:5001/health > /dev/null 2>&1; then
        print_success "Embedding service is running"
        return 0
    else
        print_error "Embedding service is not running"
        print_info "Starting embedding service..."
        
        cd "$PROJECT_ROOT"
        ./scripts/start-services.sh
        
        # Wait for service to be ready
        sleep 5
        
        if curl -s http://127.0.0.1:5001/health > /dev/null 2>&1; then
            print_success "Embedding service started"
            return 0
        else
            print_error "Failed to start embedding service"
            return 1
        fi
    fi
}

# ============================================================================
# COMPONENT TESTS
# ============================================================================

test_database() {
    print_step "Testing database operations..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if npx tsx tests/validation/test-database.ts >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Database tests passed (${duration}s)"
        update_report "Database" "SQLite Operations" "passed" "$duration" "CRUD and FTS5 working"
        return 0
    else
        duration=$(end_timer)
        print_error "Database tests failed (${duration}s)"
        update_report "Database" "SQLite Operations" "failed" "$duration" "Check logs"
        return 1
    fi
}

test_vector_store() {
    print_step "Testing vector store operations..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if npx tsx tests/validation/test-vector-store.ts >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Vector store tests passed (${duration}s)"
        update_report "VectorStore" "LanceDB Operations" "passed" "$duration" "Add and search working"
        return 0
    else
        duration=$(end_timer)
        print_error "Vector store tests failed (${duration}s)"
        update_report "VectorStore" "LanceDB Operations" "failed" "$duration" "Check logs"
        return 1
    fi
}

test_embedding_service() {
    print_step "Testing embedding service..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if npx tsx tests/validation/test-embedding-service.ts >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Embedding service tests passed (${duration}s)"
        update_report "EmbeddingService" "HTTP Client" "passed" "$duration" "Single and batch working"
        return 0
    else
        duration=$(end_timer)
        print_error "Embedding service tests failed (${duration}s)"
        update_report "EmbeddingService" "HTTP Client" "failed" "$duration" "Check logs"
        return 1
    fi
}

test_mcp_tools() {
    print_step "Testing MCP tools..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if npx tsx tests/validation/test-mcp-tools.ts >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "MCP tools tests passed (${duration}s)"
        update_report "MCPTools" "Store and Search" "passed" "$duration" "Both tools working"
        return 0
    else
        duration=$(end_timer)
        print_error "MCP tools tests failed (${duration}s)"
        update_report "MCPTools" "Store and Search" "failed" "$duration" "Check logs"
        return 1
    fi
}

test_end_to_end() {
    print_step "Testing end-to-end workflows..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if npx tsx tests/validation/test-end-to-end.ts >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "End-to-end tests passed (${duration}s)"
        update_report "Integration" "E2E Workflows" "passed" "$duration" "Store-search cycle working"
        return 0
    else
        duration=$(end_timer)
        print_error "End-to-end tests failed (${duration}s)"
        update_report "Integration" "E2E Workflows" "failed" "$duration" "Check logs"
        return 1
    fi
}

test_performance() {
    print_step "Running performance benchmarks..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if npx tsx tests/validation/test-performance.ts >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Performance benchmarks completed (${duration}s)"
        update_report "Performance" "Benchmarks" "passed" "$duration" "Within acceptable limits"
        return 0
    else
        duration=$(end_timer)
        print_warning "Performance benchmarks had warnings (${duration}s)"
        update_report "Performance" "Benchmarks" "warning" "$duration" "Some metrics exceeded targets"
        return 0  # Don't fail on performance warnings
    fi
}

# ============================================================================
# CLI TESTS
# ============================================================================

test_cli() {
    print_step "Testing CLI commands..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    # Test store command
    local test_content="CLI test memory $(date +%s)"
    if node dist/cli.js store \
        --content "$test_content" \
        --type note \
        --source manual \
        --importance medium >> "$LOG_FILE" 2>&1; then
        print_success "CLI store command works"
    else
        print_error "CLI store command failed"
        return 1
    fi
    
    # Test search command
    if node dist/cli.js search --query "CLI test" --limit 5 >> "$LOG_FILE" 2>&1; then
        print_success "CLI search command works"
    else
        print_error "CLI search command failed"
        return 1
    fi
    
    # Test stats command
    if node dist/cli.js stats >> "$LOG_FILE" 2>&1; then
        print_success "CLI stats command works"
    else
        print_error "CLI stats command failed"
        return 1
    fi
    
    # Test health command
    if node dist/cli.js health >> "$LOG_FILE" 2>&1; then
        print_success "CLI health command works"
    else
        print_error "CLI health command failed"
        return 1
    fi
    
    duration=$(end_timer)
    update_report "CLI" "All Commands" "passed" "$duration" "Store, search, stats, health working"
    return 0
}

# ============================================================================
# MAIN VALIDATION FLOW
# ============================================================================

main() {
    # Clear previous logs
    > "$LOG_FILE"
    
    print_header "${ROCKET} Phase 1 Implementation Validation"
    
    echo -e "${BOLD}MCP Agent Memory Pro - Foundation Layer${NC}"
    echo "Started at:  $(date)"
    echo "Log file: $LOG_FILE"
    echo ""
    
    # Initialize report
    init_report
    
    # Start total timer
    start_timer
    
    # Track failures
    FAILED=0
    
    # ========================================================================
    # STEP 1: Prerequisites
    # ========================================================================
    
    print_header "Step 1: Prerequisites"
    
    check_build || { FAILED=$((FAILED + 1)); }
    check_services || { FAILED=$((FAILED + 1)); }
    
    if [ $FAILED -gt 0 ]; then
        print_error "Prerequisites not met"
        exit 1
    fi
    
    # ========================================================================
    # STEP 2: Component Tests
    # ========================================================================
    
    print_header "Step 2: Component Tests"
    
    TEST_FAILURES=0
    
    test_database || TEST_FAILURES=$((TEST_FAILURES + 1))
    test_vector_store || TEST_FAILURES=$((TEST_FAILURES + 1))
    test_embedding_service || TEST_FAILURES=$((TEST_FAILURES + 1))
    test_mcp_tools || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    # ========================================================================
    # STEP 3: Integration Tests
    # ========================================================================
    
    print_header "Step 3: Integration Tests"
    
    test_end_to_end || TEST_FAILURES=$((TEST_FAILURES + 1))
    test_cli || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    # ========================================================================
    # STEP 4: Performance Tests
    # ========================================================================
    
    print_header "Step 4: Performance Benchmarks"
    
    test_performance || true  # Don't count as failure
    
    # ========================================================================
    # STEP 5: Summary
    # ========================================================================
    
    TOTAL_DURATION=$(end_timer)
    
    print_header "Validation Summary"
    
    # Read and display report
    python3 <<EOF
import json

with open('$REPORT_FILE', 'r') as f:
    report = json.load(f)

summary = report['summary']
print(f"Total Tests:     {summary['total_tests']}")
print(f"${GREEN}Passed:${NC}        {summary['passed']}")
print(f"${RED}Failed: ${NC}        {summary['failed']}")
print(f"${YELLOW}Warnings:${NC}      {summary['warnings']}")
print(f"\nDuration:        {report['duration_seconds']}s")

print("\n${BOLD}Component Breakdown:${NC}\n")
for component in report['components']:
    comp_passed = sum(1 for t in component['tests'] if t['status'] == 'passed')
    comp_total = len(component['tests'])
    status = "${GREEN}✓${NC}" if comp_passed == comp_total else "${RED}✗${NC}"
    print(f"{status} {component['name']}:  {comp_passed}/{comp_total}")
EOF
    
    echo ""
    print_info "Detailed report:  $REPORT_FILE"
    print_info "Full log: $LOG_FILE"
    echo ""
    
    # Finalize report
    if [ $TEST_FAILURES -eq 0 ]; then
        finalize_report "$TOTAL_DURATION" "passed"
        print_header "${CHECK} All Validations Passed!"
        echo ""
        echo -e "${GREEN}${BOLD}Phase 1 implementation is complete and working!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Configure Claude Desktop (see README.md)"
        echo "  2. Test with Claude"
        echo "  3. Proceed to Phase 2 planning"
        echo ""
        exit 0
    else
        finalize_report "$TOTAL_DURATION" "failed"
        print_header "${CROSS} Validation Failed"
        echo ""
        echo -e "${RED}$TEST_FAILURES test(s) failed${NC}"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check the log:  $LOG_FILE"
        echo "  2. Review the report: $REPORT_FILE"
        echo "  3. Run individual tests: npx tsx tests/validation/test-*. ts"
        echo "  4. Check service status: npm run cli health"
        echo ""
        exit 2
    fi
}

# ============================================================================
# EXECUTION
# ============================================================================

trap 'echo -e "\n${RED}ERROR:  Validation script failed unexpectedly${NC}"; exit 3' ERR

main
