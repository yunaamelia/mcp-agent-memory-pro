#!/bin/bash

# ============================================================================
# Restore Script
# Restores data from backup
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Error: No backup file specified${NC}"
    echo ""
    echo "Usage: ./scripts/restore.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh "$PROJECT_ROOT/backups/" 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error:  Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This will REPLACE all existing data!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no) " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo "Restoring from backup..."
echo "  Backup file: $BACKUP_FILE"
echo ""

# Stop workers
"$SCRIPT_DIR/stop-workers.sh" 2>/dev/null || true

# Use Python import service
cd "$PROJECT_ROOT"
if [ -d "python/venv" ]; then
    source python/venv/bin/activate
fi

python3 <<EOF
import sys
sys. path.append('python')

from data_management.import_service import ImportService
import sqlite3
import os

db_path = os.getenv('MCP_MEMORY_DB_PATH', 'data/memories.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

service = ImportService(conn)
result = service.restore_full_backup('$BACKUP_FILE')

print(f"✓ Restore completed successfully")
print(f"  Memories restored: {result['memories_restored']}")
print(f"  Entities restored: {result['entities_restored']}")
print(f"  Relationships restored: {result['relationships_restored']}")

conn.close()
EOF

echo ""
echo -e "${GREEN}Restore complete!${NC}"
echo ""
echo "You can now restart workers:  ./scripts/start-workers.sh"
echo ""
