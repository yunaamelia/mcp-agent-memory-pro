#!/usr/bin/env python3
"""
Test Export and Import
"""

import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from data_management.export_service import ExportService
from data_management.import_service import ImportService


def test_export_import():
    """Test export and import functionality"""

    print("Testing Export/Import")
    print("=" * 60)

    # Create test database
    test_db = Path(__file__).parent.parent / "validation" / "test_export.db"
    test_db.parent.mkdir(parents=True, exist_ok=True)
    if test_db.exists():
        test_db.unlink()

    conn = sqlite3.connect(str(test_db))
    conn.row_factory = sqlite3.Row

    # Create table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            tier TEXT,
            type TEXT,
            source TEXT,
            content TEXT,
            content_hash TEXT,
            timestamp INTEGER,
            project TEXT,
            file_path TEXT,
            language TEXT,
            tags TEXT,
            entities TEXT,
            importance_score REAL,
            access_count INTEGER,
            created_at INTEGER,
            last_accessed INTEGER,
            promoted_from TEXT,
            archived INTEGER
        )
    """)

    # Mock other tables to avoid errors in full backup
    conn.execute(
        "CREATE TABLE IF NOT EXISTS entities (id TEXT, type TEXT, name TEXT, first_seen INTEGER, last_seen INTEGER, mention_count INTEGER)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS entity_relationships (source_id TEXT, target_id TEXT, type TEXT, strength REAL, created_at INTEGER, updated_at INTEGER)"
    )
    conn.execute("CREATE TABLE IF NOT EXISTS statistics (key TEXT, value TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS memory_entities (memory_id TEXT, entity_id TEXT)")

    # Insert test data
    now = int(datetime.now(UTC).timestamp() * 1000)

    conn.execute(
        """
        INSERT INTO memories VALUES (
            'export_test_1', 'short', 'code', 'ide',
            'function test() {}', 'hash1', ?, 'test-project',
            NULL, 'javascript', '["test"]', NULL, 0.8, 0, ?, ?, NULL, 0
        )
    """,
        (now, now, now),
    )

    conn.commit()

    # Test export to JSON
    print("\n1. Testing JSON export...")

    export_service = ExportService(conn)
    export_path = test_db.parent / "export_test.json"

    result = export_service.export_to_json(str(export_path))

    print(f"  ✓ Exported {result['count']} memories")
    print(f"    Size: {result['size_bytes']} bytes")

    # Verify export file
    with open(export_path) as f:
        exported_data = json.load(f)

    assert len(exported_data["memories"]) == 1
    print("  ✓ Export file verified")

    # Test import
    print("\n2. Testing JSON import...")

    # Clear database
    conn.execute("DELETE FROM memories")
    conn.commit()

    import_service = ImportService(conn)
    result = import_service.import_from_json(str(export_path))

    print(f"  ✓ Imported {result['imported']} memories")

    # Verify import
    cursor = conn.execute("SELECT COUNT(*) as count FROM memories")
    count = cursor.fetchone()["count"]

    assert count == 1
    print("  ✓ Import verified")

    # Cleanup
    conn.close()
    if test_db.exists():
        test_db.unlink()
    if export_path.exists():
        export_path.unlink()

    print("\n✅ Export/Import tests passed!")


if __name__ == "__main__":
    test_export_import()
