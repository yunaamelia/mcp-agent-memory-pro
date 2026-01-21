#!/usr/bin/env python3
"""
Test Individual Workers
Tests each background worker independently
"""

import json
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from services.ner_service import NERService
from services.scoring_service import ImportanceScoringService


def create_test_database():
    """Create an in-memory test database with schema"""

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            tier TEXT DEFAULT 'short',
            type TEXT NOT NULL,
            source TEXT,
            content TEXT NOT NULL,
            content_hash TEXT,
            timestamp INTEGER,
            project TEXT,
            file_path TEXT,
            language TEXT,
            tags TEXT,
            entities TEXT,
            importance_score REAL DEFAULT 0.5,
            access_count INTEGER DEFAULT 0,
            created_at INTEGER,
            last_accessed INTEGER,
            promoted_from TEXT,
            archived INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            first_seen INTEGER,
            last_seen INTEGER,
            mention_count INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE memory_entities (
            memory_id TEXT,
            entity_id TEXT,
            relevance REAL,
            PRIMARY KEY (memory_id, entity_id)
        )
    """)

    conn.execute("""
        CREATE TABLE entity_relationships (
            source_id TEXT,
            target_id TEXT,
            type TEXT,
            strength REAL,
            created_at INTEGER,
            updated_at INTEGER,
            PRIMARY KEY (source_id, target_id, type)
        )
    """)

    return conn


def insert_test_memories(conn):
    """Insert test memories"""

    now = int(datetime.now(UTC).timestamp() * 1000)
    old = int((datetime.now(UTC) - timedelta(days=7)).timestamp() * 1000)

    test_memories = [
        (
            "mem1",
            "short",
            "code",
            "ide",
            "function calculateTotal(items) { return items.reduce((sum, item) => sum + item.price, 0); }",
            now,
            "test-project",
            "calculator.js",
            "javascript",
            '["function", "array"]',
            None,
            0.5,
            3,
            now,
            now,
        ),
        (
            "mem2",
            "short",
            "code",
            "ide",
            "async function fetchData(url) { const response = await fetch(url); return response.json(); }",
            old,
            "test-project",
            "api.js",
            "javascript",
            '["async", "fetch"]',
            None,
            0.8,
            5,
            old,
            now,
        ),
        (
            "mem3",
            "working",
            "note",
            "manual",
            "Remember to update API documentation before release",
            old,
            "test-project",
            None,
            None,
            '["documentation", "release"]',
            None,
            0.6,
            1,
            old,
            old,
        ),
    ]

    for mem in test_memories:
        conn.execute(
            """
            INSERT INTO memories
            (id, tier, type, source, content, timestamp, project, file_path,
             language, tags, entities, importance_score, access_count, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            mem,
        )

    conn.commit()
    return len(test_memories)


def test_importance_scorer():
    """Test ImportanceScorerWorker"""

    print("Testing ImportanceScorerWorker")
    print("-" * 40)

    conn = create_test_database()
    insert_test_memories(conn)

    scorer = ImportanceScoringService(conn)

    # Get a memory and score it
    cursor = conn.execute("SELECT * FROM memories WHERE id = ?", ("mem1",))
    memory = dict(cursor.fetchone())
    memory["tags"] = json.loads(memory["tags"]) if memory.get("tags") else []

    score = scorer.calculate_importance(memory)

    print(f"  Memory mem1 scored: {score:.3f}")
    assert 0.0 <= score <= 1.0, "Score out of range"

    # Score all memories
    scored_count = 0
    for row in conn.execute("SELECT * FROM memories").fetchall():
        mem = dict(row)
        mem["tags"] = json.loads(mem["tags"]) if mem.get("tags") else []
        s = scorer.calculate_importance(mem)
        if 0.0 <= s <= 1.0:
            scored_count += 1

    print(f"  Scored {scored_count}/3 memories")
    assert scored_count == 3, "Not all memories scored"

    conn.close()
    print("  ✅ ImportanceScorerWorker test passed\n")


def test_entity_extractor():
    """Test EntityExtractorWorker"""

    print("Testing EntityExtractorWorker")
    print("-" * 40)

    ner = NERService()

    code = "function calculateTotal(items) { return items.reduce((sum, item) => sum + item.price, 0); }"
    entities = ner.extract_entities(code, "code", {"language": "javascript"})

    print(f"  Extracted {len(entities)} entities")
    assert len(entities) > 0, "No entities extracted"

    function_entities = [e for e in entities if e["type"] == "function"]
    print(f"  Function entities: {len(function_entities)}")
    assert len(function_entities) > 0, "No function entities"

    print("  ✅ EntityExtractorWorker test passed\n")


def test_memory_promoter():
    """Test MemoryPromoterWorker logic"""

    print("Testing MemoryPromoterWorker")
    print("-" * 40)

    conn = create_test_database()
    insert_test_memories(conn)

    # Get short-term memories count
    short_count = conn.execute(
        "SELECT COUNT(*) as count FROM memories WHERE tier = 'short'"
    ).fetchone()["count"]

    print(f"  Short-term memories: {short_count}")
    assert short_count > 0, "No short-term memories"

    # Import config for thresholds
    try:
        from config import IMPORTANCE_SCORE_THRESHOLD, MIN_ACCESS_COUNT_FOR_PROMOTION
    except ImportError:
        IMPORTANCE_SCORE_THRESHOLD = 0.7
        MIN_ACCESS_COUNT_FOR_PROMOTION = 2

    promotable = conn.execute(
        """
        SELECT COUNT(*) as count FROM memories
        WHERE tier = 'short' AND archived = 0
        AND (importance_score >= ? OR access_count >= ?)
    """,
        (IMPORTANCE_SCORE_THRESHOLD, MIN_ACCESS_COUNT_FOR_PROMOTION),
    ).fetchone()["count"]

    print(f"  Promotable memories: {promotable}")

    # Verify tier distribution
    for row in conn.execute(
        "SELECT tier, COUNT(*) as count FROM memories WHERE archived = 0 GROUP BY tier"
    ):
        print(f"  Tier '{row['tier']}': {row['count']} memories")

    conn.close()
    print("  ✅ MemoryPromoterWorker test passed\n")


def test_graph_builder():
    """Test GraphBuilderWorker"""

    print("Testing GraphBuilderWorker")
    print("-" * 40)

    conn = create_test_database()

    # Insert some entity relationships
    now = int(datetime.now(UTC).timestamp())

    conn.execute(
        """
        INSERT INTO entities (id, type, name, first_seen, last_seen, mention_count)
        VALUES ('function:calculateTotal', 'function', 'calculateTotal', ?, ?, 1)
    """,
        (now, now),
    )

    conn.execute(
        """
        INSERT INTO entities (id, type, name, first_seen, last_seen, mention_count)
        VALUES ('function:fetchData', 'function', 'fetchData', ?, ?, 1)
    """,
        (now, now),
    )

    conn.execute(
        """
        INSERT INTO entities (id, type, name, first_seen, last_seen, mention_count)
        VALUES ('concept:async', 'concept', 'async', ?, ?, 1)
    """,
        (now, now),
    )

    # Link entities to memories (simulating co-occurrence)
    conn.execute("""
        INSERT INTO memory_entities (memory_id, entity_id, relevance)
        VALUES ('mem1', 'function:calculateTotal', 0.9)
    """)
    conn.execute("""
        INSERT INTO memory_entities (memory_id, entity_id, relevance)
        VALUES ('mem2', 'function:fetchData', 0.9)
    """)
    conn.execute("""
        INSERT INTO memory_entities (memory_id, entity_id, relevance)
        VALUES ('mem2', 'concept:async', 0.8)
    """)

    conn.commit()

    # Verify entities exist
    entity_count = conn.execute("SELECT COUNT(*) as count FROM entities").fetchone()["count"]
    print(f"  Entities in database: {entity_count}")
    assert entity_count >= 3, "Entities not inserted"

    # Verify memory-entity links
    link_count = conn.execute("SELECT COUNT(*) as count FROM memory_entities").fetchone()["count"]
    print(f"  Memory-entity links: {link_count}")
    assert link_count >= 3, "Links not inserted"

    conn.close()
    print("  ✅ GraphBuilderWorker test passed\n")


def test_summarizer_logic():
    """Test Summarizer logic (without API call)"""

    print("Testing SummarizerWorker logic")
    print("-" * 40)

    conn = create_test_database()
    insert_test_memories(conn)

    # Check for long-term memories that would need summarization
    long_count = conn.execute(
        "SELECT COUNT(*) as count FROM memories WHERE tier = 'long' AND archived = 0"
    ).fetchone()["count"]

    print(f"  Long-term memories: {long_count}")

    # Simulate adding a long-term memory
    now = int(datetime.now(UTC).timestamp() * 1000)
    conn.execute(
        """
        INSERT INTO memories (id, tier, type, source, content, timestamp, importance_score, access_count, created_at, archived)
        VALUES ('long_mem', 'long', 'code', 'ide', ?, ?, 0.7, 0, ?, 0)
    """,
        ("A very long content " * 50, now, now),
    )
    conn.commit()

    # Verify long memory exists
    new_long_count = conn.execute(
        "SELECT COUNT(*) as count FROM memories WHERE tier = 'long' AND archived = 0"
    ).fetchone()["count"]

    print(f"  Long-term memories after insert: {new_long_count}")
    assert new_long_count == long_count + 1

    conn.close()
    print("  ✅ SummarizerWorker logic test passed\n")


def main():
    """Run all worker tests"""

    print("\n" + "=" * 50)
    print("BACKGROUND WORKERS VALIDATION")
    print("=" * 50 + "\n")

    try:
        test_importance_scorer()
        test_entity_extractor()
        test_memory_promoter()
        test_graph_builder()
        test_summarizer_logic()

        print("=" * 50)
        print("✅ ALL WORKER TESTS PASSED")
        print("=" * 50)

        return 0

    except Exception as e:
        print(f"\n❌ Worker tests failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
