#!/bin/bash

# ============================================================================
# Convenience wrapper for Phase 2 validation
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

exec "$PROJECT_ROOT/tests/validation/phase2-validate.sh" "$@"
