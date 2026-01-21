#!/usr/bin/env python3
"""
Test Importance Scorer Worker
"""

import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from services.scoring_service import ImportanceScoringService


def test_importance_scoring():
    """Test importance scoring logic"""

    print("Testing Importance Scoring Service")
    print("=" * 50)

    # Create temporary database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Create minimal schema
    conn.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT,
            source TEXT,
            content TEXT,
            timestamp INTEGER,
            access_count INTEGER,
            created_at INTEGER,
            project TEXT,
            file_path TEXT,
            tags TEXT,
            importance_score REAL
        )
    """)

    # Insert test memories
    now = int(datetime.now(UTC).timestamp() * 1000)

    test_memories = [
        {
            "id": "test1",
            "type": "code",
            "source": "ide",
            "content": "function authenticateUser(credentials) { return jwt.sign(credentials); }",
            "timestamp": now,
            "access_count": 5,
            "created_at": now,
            "project": "test-app",
            "tags": '["auth", "security"]',
        },
        {
            "id": "test2",
            "type": "command",
            "source": "terminal",
            "content": "ls -la",
            "timestamp": now - (7 * 24 * 60 * 60 * 1000),
            "access_count": 0,
            "created_at": now - (7 * 24 * 60 * 60 * 1000),
            "project": None,
            "tags": None,
        },
    ]

    for mem in test_memories:
        conn.execute(
            """
            INSERT INTO memories
            (id, type, source, content, timestamp, access_count, created_at, project, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                mem["id"],
                mem["type"],
                mem["source"],
                mem["content"],
                mem["timestamp"],
                mem["access_count"],
                mem["created_at"],
                mem["project"],
                mem["tags"],
            ),
        )

    conn.commit()

    # Test scoring
    scorer = ImportanceScoringService(conn)

    for mem_id in ["test1", "test2"]:
        cursor = conn.execute("SELECT * FROM memories WHERE id = ?", (mem_id,))
        memory = dict(cursor.fetchone())

        if memory.get("tags"):
            import json

            try:
                memory["tags"] = json.loads(memory["tags"])
            except Exception:
                memory["tags"] = []

        score = scorer.calculate_importance(memory)

        print(f"\nMemory: {mem_id}")
        print(f"  Type: {memory['type']}")
        print(f"  Source: {memory['source']}")
        print(f"  Access count: {memory['access_count']}")
        print(f"  Importance score: {score:.3f}")

    conn.close()

    print("\n✅ Importance scoring test passed!")


if __name__ == "__main__":
    test_importance_scoring()
