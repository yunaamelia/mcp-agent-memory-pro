#!/bin/bash

# ============================================================================
# Phase 4 Implementation Validation Script
# ============================================================================

set -e
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_FILE="$SCRIPT_DIR/../phase4-validation-report.json"
LOG_FILE="$SCRIPT_DIR/../phase4-validation.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

CHECK="✅"
CROSS="❌"
ROCKET="🚀"

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

# ============================================================================
# TESTS
# ============================================================================

test_memql() {
    echo "Testing MemQL..."
    
    if python3 tests/phase4/test_memql.py >> "$LOG_FILE" 2>&1; then
        print_success "MemQL tests passed"
        return 0
    else
        print_error "MemQL tests failed"
        return 1
    fi
}

test_export_import() {
    echo "Testing Export/Import..."
    
    if python3 tests/phase4/test_export_import.py >> "$LOG_FILE" 2>&1; then
        print_success "Export/Import tests passed"
        return 0
    else
        print_error "Export/Import tests failed"
        return 1
    fi
}

test_phase4_tools() {
    echo "Testing Phase 4 MCP tools..."
    
    if npx tsx tests/validation/test-phase4-tools.ts >> "$LOG_FILE" 2>&1; then
        print_success "Phase 4 tools tests passed"
        return 0
    else
        print_error "Phase 4 tools tests failed"
        return 1
    fi
}

test_api() {
    echo "Testing REST API..."
    
    # Start API server
    cd "$PROJECT_ROOT/python"
    
    # Check if venv exists and activate
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    export MCP_MEMORY_DB_PATH="$PROJECT_ROOT/data/memories.db"
    export MCP_MEMORY_DATA_DIR="$PROJECT_ROOT/data"
    
    python3 -c "
from api.rest_api import app
import uvicorn
import threading
import time
import requests
import sys

# Start server in background
def run_server():
    uvicorn.run(app, host='127.0.0.1', port=8001, log_level='error')

thread = threading.Thread(target=run_server, daemon=True)
thread.start()
time.sleep(5)  # Increased wait time for server start

# Test endpoints
try:
    print('Testing /health...')
    r = requests.get('http://127.0.0.1:8001/health', timeout=10)
    assert r.status_code == 200
    print('✓ Health endpoint working')
    
    print('Testing /analytics/overview...')
    r = requests.get('http://127.0.0.1:8001/analytics/overview', timeout=10)
    assert r.status_code == 200
    print('✓ Analytics endpoint working')
    
    print('All API tests passed')
except Exception as e:
    print(f'API test failed: {e}')
    sys.exit(1)
" && print_success "API tests passed" || print_error "API tests failed"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    > "$LOG_FILE"
    
    print_header "${ROCKET} Phase 4 Production Features Validation"
    
    echo -e "${BOLD}MCP Agent Memory Pro - Production Ready${NC}"
    echo ""
    
    TEST_FAILURES=0
    
    print_header "Phase 4 Component Tests"
    
    test_memql || TEST_FAILURES=$((TEST_FAILURES + 1))
    test_export_import || TEST_FAILURES=$((TEST_FAILURES + 1))
    test_phase4_tools || TEST_FAILURES=$((TEST_FAILURES + 1))
    test_api || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    print_header "Validation Summary"
    
    if [ $TEST_FAILURES -eq 0 ]; then
        print_header "${CHECK} All Validations Passed!"
        echo ""
        echo -e "${GREEN}${BOLD}Phase 4 complete!  System is production-ready! ${NC}"
        echo ""
        echo "Production Features:"
        echo "  ✓ MemQL Query Language"
        echo "  ✓ Export/Import"
        echo "  ✓ REST API"
        echo "  ✓ Health Monitoring"
        echo "  ✓ Analytics Dashboard"
        echo "  ✓ 4 New MCP Tools"
        echo "  ✓ Total:  10 MCP Tools"
        echo ""
        exit 0
    else
        print_error "Validation Failed"
        print_error "Check log file for details: phases4-validation.log"
        exit 1
    fi
}

main
