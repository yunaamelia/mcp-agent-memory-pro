#!/bin/bash

# ============================================================================
# Cleanup Script - Remove test data and temporary files
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧹 Cleaning up Phase 0 test data..."
echo ""

# Remove PoC data
if [ -d "$PROJECT_ROOT/poc/data" ]; then
    rm -rf "$PROJECT_ROOT/poc/data"
    echo "✓ Removed poc/data/"
fi

# Remove logs
rm -f "$PROJECT_ROOT/poc/validation.log" 2>/dev/null && echo "✓ Removed validation.log"
rm -f "$PROJECT_ROOT/poc/validation-report.json" 2>/dev/null && echo "✓ Removed validation-report.json"

# Remove temporary files
rm -f "$PROJECT_ROOT/poc/temp_server.py" 2>/dev/null

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To clean node_modules: rm -rf node_modules && npm install"
echo "To clean Python venv: rm -rf poc/venv"
