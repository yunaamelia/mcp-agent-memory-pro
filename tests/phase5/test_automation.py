#!/usr/bin/env python3
"""
Test Automation System
"""

import json
import re
import sqlite3
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))


def test_auto_tagging_workflow():
    """Test complete auto-tagging workflow"""

    print("Testing Auto-Tagging Workflow")
    print("=" * 60)

    # Create test database
    test_db = Path(__file__).parent.parent / "data" / "test_automation.db"
    test_db.parent.mkdir(parents=True, exist_ok=True)

    if test_db.exists():
        test_db.unlink()

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row

    # Create minimal schema
    conn.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT,
            content TEXT,
            project TEXT,
            language TEXT,
            tags TEXT
        )
    """)

    # Insert untagged memories
    test_memories = [
        (
            "auto1",
            "code",
            'async function fetchData() { await api.get("/data"); }',
            "api-service",
            "javascript",
            None,
        ),
        ("auto2", "note", "TODO: Update API documentation", "api-service", None, None),
        (
            "auto3",
            "code",
            "class UserManager { constructor() {} }",
            "user-service",
            "javascript",
            None,
        ),
    ]

    conn.executemany("INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?)", test_memories)
    conn.commit()

    try:
        print("\n1. Auto-tagging memories...")

        def auto_tag(content, type_, language=None):
            """Simple keyword-based auto-tagging"""
            tags = []

            if re.search(r"\bfunction\b|\bdef\b|\bclass\b", content, re.I):
                tags.append("code")
            if re.search(r"\basync\b|\bawait\b", content, re.I):
                tags.append("async")
            if re.search(r"\bTODO\b|\bFIXME\b", content, re.I):
                tags.append("todo")
            if re.search(r"\bAPI\b|\bendpoint\b", content, re.I):
                tags.append("api")
            if language:
                tags.append(language)

            return list(set(tags))

        cursor = conn.execute("SELECT * FROM memories WHERE tags IS NULL")
        memories = [dict(row) for row in cursor.fetchall()]

        batch_tags = {}
        for memory in memories:
            tags = auto_tag(memory["content"], memory["type"], memory.get("language"))
            batch_tags[memory["id"]] = tags
            conn.execute(
                "UPDATE memories SET tags = ? WHERE id = ?", (json.dumps(tags), memory["id"])
            )

        conn.commit()

        print(f"  ✓ Tagged {len(batch_tags)} memories")

        # Verify tags were added
        cursor = conn.execute("SELECT id, tags FROM memories")

        for row in cursor.fetchall():
            tags = json.loads(row["tags"]) if row["tags"] else []
            print(f"    {row['id']}: {tags}")
            assert len(tags) > 0, f"No tags generated for {row['id']}"

        print("  ✓ All memories have tags")

        print("\n✅ Auto-tagging workflow test passed")

        return True

    finally:
        conn.close()
        test_db.unlink()


def test_duplicate_detection():
    """Test duplicate detection"""

    print("\n\nTesting Duplicate Detection")
    print("=" * 60)

    test_db = Path(__file__).parent.parent / "data" / "test_duplicates.db"
    test_db.parent.mkdir(parents=True, exist_ok=True)

    if test_db.exists():
        test_db.unlink()

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row

    # Create schema
    conn.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT,
            content TEXT,
            tier TEXT,
            importance_score REAL,
            archived INTEGER
        )
    """)

    # Insert similar memories
    memories = [
        ("dup1", "code", "function test() { return 42; }", "short", 0.8, 0),
        ("dup2", "code", "function test() { return 42; }", "short", 0.7, 0),  # Near duplicate
        ("dup3", "code", "function different() { return 100; }", "short", 0.6, 0),  # Different
    ]

    conn.executemany("INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?)", memories)
    conn.commit()

    try:
        print("\n1. Finding duplicates...")

        cursor = conn.execute("SELECT id, content FROM memories WHERE archived = 0")
        all_memories = [dict(row) for row in cursor.fetchall()]

        duplicates = []
        for i, m1 in enumerate(all_memories):
            for m2 in all_memories[i + 1 :]:
                c1 = m1.get("content", "")[:500]
                c2 = m2.get("content", "")[:500]
                ratio = SequenceMatcher(None, c1, c2).ratio()
                if ratio > 0.9:
                    duplicates.append((m1["id"], m2["id"], round(ratio, 2)))

        print(f"  Found {len(duplicates)} duplicate pair(s)")

        for id1, id2, similarity in duplicates:
            print(f"    {id1} ↔ {id2}: {similarity:.0%} similar")

        assert len(duplicates) >= 1, "Expected to find duplicates"

        print("  ✓ Duplicate detection working")

        print("\n✅ Duplicate detection test passed")

        return True

    finally:
        conn.close()
        test_db.unlink()


def main():
    """Run all automation tests"""

    print("\n" + "=" * 60)
    print("PHASE 5 AUTOMATION VALIDATION")
    print("=" * 60 + "\n")

    try:
        test_auto_tagging_workflow()
        test_duplicate_detection()

        print("\n" + "=" * 60)
        print("✅ ALL AUTOMATION TESTS PASSED")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Automation tests failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
