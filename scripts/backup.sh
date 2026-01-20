#!/bin/bash

# ============================================================================
# Backup Script
# Creates complete backup of all data
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"
BACKUP_DIR="$PROJECT_ROOT/backups"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}MCP Memory Backup${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.zip"

echo "Creating backup..."
echo "  Backup file: $BACKUP_FILE"
echo ""

# Use Python export service
cd "$PROJECT_ROOT"
# Check if venv exists, if so activate it
if [ -d "python/venv" ]; then
    source python/venv/bin/activate
fi

python3 <<EOF
import sys
sys.path.append('python')

from data_management.export_service import ExportService
import sqlite3
import os

db_path = os.getenv('MCP_MEMORY_DB_PATH', '$DATA_DIR/memories.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

service = ExportService(conn)
result = service.export_full_backup('$BACKUP_FILE')

print(f"✓ Backup created successfully")
print(f"  Memories:  {result['memory_count']}")
print(f"  Entities: {result['entity_count']}")
print(f"  Size: {result['size_bytes'] / (1024*1024):.2f} MB")

conn.close()
EOF

echo ""
echo -e "${GREEN}Backup complete!${NC}"
echo ""
echo "Backup location: $BACKUP_FILE"
echo ""
echo "To restore:  ./scripts/restore.sh $BACKUP_FILE"
echo ""
