#!/bin/bash
# Wrapper script for Phase 5 validation
# Runs the main validation suite

set -e

cd "$(dirname "$0")/.."

echo "Running Phase 5 Validation..."
echo ""

# Make scripts executable
chmod +x tests/validation/phase5-validate.sh
chmod +x tests/validation/test-extensions.sh

# Run main validation
bash tests/validation/phase5-validate.sh
