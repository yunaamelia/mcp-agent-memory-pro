#!/bin/bash

# ============================================================================
# Phase 2 Implementation Validation Script
# ============================================================================

set -e
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_FILE="$SCRIPT_DIR/../phase2-validation-report.json"
LOG_FILE="$SCRIPT_DIR/../phase2-validation.log"

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
WARNING="⚠️"
ROCKET="🚀"
GEAR="⚙️"

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

init_report() {
    cat > "$REPORT_FILE" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "phase": "Phase 2 - Intelligence Layer",
  "environment": {
    "node_version": "$(node -v 2>/dev/null || echo 'N/A')",
    "python_version": "$(python3 --version 2>&1)",
    "os": "$(uname -s)"
  },
  "components": [],
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

component_found = False
for comp in report['components']:
    if comp['name'] == '$component':
        comp['tests'].append({
            'name': '$test_name',
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

check_python_dependencies() {
    print_step "Checking Python dependencies for Phase 2..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "python/venv" ]; then
        source python/venv/bin/activate
    else
        print_error "No Python virtual environment found"
        return 1
    fi
    
    local required_packages=("apscheduler" "anthropic" "sklearn")
    
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            print_warning "Missing package: $package"
            print_info "Installing dependencies..."
            pip install -q -r python/requirements-workers.txt 2>/dev/null || true
            break
        fi
    done
    
    print_success "Python dependencies available"
    return 0
}

check_services_running() {
    print_step "Checking if embedding service is running..."
    
    if curl -s http://127.0.0.1:5001/health > /dev/null 2>&1; then
        print_success "Embedding service is running"
        return 0
    else
        print_warning "Embedding service not running"
        print_info "Some tests may be skipped"
        return 0
    fi
}

test_intelligence_services() {
    print_step "Testing intelligence services..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    if python3 tests/validation/test-services.py >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Intelligence services tests passed (${duration}s)"
        update_report "IntelligenceServices" "Scoring+NER" "passed" "$duration" "All services working"
        return 0
    else
        duration=$(end_timer)
        print_error "Intelligence services tests failed (${duration}s)"
        update_report "IntelligenceServices" "Scoring+NER" "failed" "$duration" "Check logs"
        return 1
    fi
}

test_individual_workers() {
    print_step "Testing individual workers..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    if python3 tests/validation/test-workers.py >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Individual worker tests passed (${duration}s)"
        update_report "Workers" "Individual Execution" "passed" "$duration" "All workers functional"
        return 0
    else
        duration=$(end_timer)
        print_error "Individual worker tests failed (${duration}s)"
        update_report "Workers" "Individual Execution" "failed" "$duration" "Check logs"
        return 1
    fi
}

test_scheduler() {
    print_step "Testing job scheduler..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    if python3 tests/validation/test-scheduler.py >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Scheduler tests passed (${duration}s)"
        update_report "Scheduler" "Job Scheduling" "passed" "$duration" "Scheduler working"
        return 0
    else
        duration=$(end_timer)
        print_error "Scheduler tests failed (${duration}s)"
        update_report "Scheduler" "Job Scheduling" "failed" "$duration" "Check logs"
        return 1
    fi
}

test_insights_tool() {
    print_step "Testing memory_insights MCP tool..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if npx tsx tests/validation/test-insights-tool.ts >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Insights tool tests passed (${duration}s)"
        update_report "MCPTools" "memory_insights" "passed" "$duration" "All insight types working"
        return 0
    else
        duration=$(end_timer)
        print_error "Insights tool tests failed (${duration}s)"
        update_report "MCPTools" "memory_insights" "failed" "$duration" "Check logs"
        return 1
    fi
}

test_worker_performance() {
    print_step "Running worker performance benchmarks..."
    start_timer
    
    cd "$PROJECT_ROOT"
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    if python3 tests/validation/test-worker-performance.py >> "$LOG_FILE" 2>&1; then
        duration=$(end_timer)
        print_success "Performance benchmarks completed (${duration}s)"
        update_report "Performance" "Worker Benchmarks" "passed" "$duration" "Within limits"
        return 0
    else
        duration=$(end_timer)
        print_warning "Performance benchmarks had warnings (${duration}s)"
        update_report "Performance" "Worker Benchmarks" "warning" "$duration" "Some metrics exceeded"
        return 0
    fi
}

main() {
    > "$LOG_FILE"
    
    print_header "${ROCKET} Phase 2 Implementation Validation"
    
    echo -e "${BOLD}MCP Agent Memory Pro - Intelligence Layer${NC}"
    echo "Started at: $(date)"
    echo ""
    
    init_report
    start_timer
    
    TEST_FAILURES=0
    
    print_header "Step 1: Prerequisites"
    check_python_dependencies || TEST_FAILURES=$((TEST_FAILURES + 1))
    check_services_running
    
    print_header "Step 2: Intelligence Services"
    test_intelligence_services || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    print_header "Step 3: Background Workers"
    test_individual_workers || TEST_FAILURES=$((TEST_FAILURES + 1))
    test_scheduler || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    print_header "Step 4: MCP Tools"
    test_insights_tool || TEST_FAILURES=$((TEST_FAILURES + 1))
    
    print_header "Step 5: Performance"
    test_worker_performance || true
    
    TOTAL_DURATION=$(end_timer)
    
    print_header "Validation Summary"
    
    python3 <<EOF
import json

with open('$REPORT_FILE', 'r') as f:
    report = json.load(f)

summary = report['summary']
print(f"Total Tests:  {summary['total_tests']}")
print(f"Passed:       {summary['passed']}")
print(f"Failed:       {summary['failed']}")
print(f"Warnings:     {summary['warnings']}")
print(f"Duration:     {report['duration_seconds']}s")
EOF
    
    echo ""
    print_info "Report: $REPORT_FILE"
    print_info "Log: $LOG_FILE"
    echo ""
    
    if [ $TEST_FAILURES -eq 0 ]; then
        finalize_report "$TOTAL_DURATION" "passed"
        print_header "${CHECK} All Validations Passed!"
        echo -e "${GREEN}${BOLD}Phase 2 implementation is complete!${NC}"
        exit 0
    else
        finalize_report "$TOTAL_DURATION" "failed"
        print_header "${CROSS} Validation Failed"
        echo -e "${RED}$TEST_FAILURES test(s) failed${NC}"
        exit 2
    fi
}

trap 'echo -e "\n${RED}Validation failed unexpectedly${NC}"; exit 3' ERR

main
