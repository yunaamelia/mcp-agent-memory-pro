import logging
import os
import sqlite3
import sys
from datetime import UTC, datetime, timedelta

# Add python directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from workers.importance_scorer import ImportanceScorerWorker  # noqa: E402


def setup_test_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    # Create memories table if not exists (simplified schema for testing)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            type TEXT,
            content TEXT,
            source TEXT,
            timestamp TEXT,
            created_at TEXT,
            access_count INTEGER DEFAULT 0,
            importance_score REAL,
            archived INTEGER DEFAULT 0,
            project TEXT,
            file_path TEXT,
            tags TEXT
        )
    """)

    # Insert test data
    memories = [
        (
            "mem_1",
            "text",
            "Short content",
            "user",
            datetime.now(UTC).isoformat(),
            datetime.now(UTC).isoformat(),
            1,
            None,
            0,
            "test",
            "path/1",
            "[]",
        ),
        (
            "mem_2",
            "code_snippet",
            "def complex_function():\n    pass\n    return True" * 20,
            "agent",
            (datetime.now(UTC) - timedelta(days=1)).isoformat(),
            datetime.now(UTC).isoformat(),
            50,
            0.5,
            0,
            "test",
            "path/2",
            '["important"]',
        ),
        (
            "mem_3",
            "text",
            "Old content",
            "system",
            (datetime.now(UTC) - timedelta(days=30)).isoformat(),
            datetime.now(UTC).isoformat(),
            0,
            None,
            0,
            "test",
            "path/3",
            "[]",
        ),
    ]

    for mem in memories:
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO memories
                (id, type, content, source, timestamp, created_at, access_count, importance_score, archived, project, file_path, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                mem,
            )
        except Exception as e:
            print(f"Error inserting {mem[0]}: {e}")

    conn.commit()
    return conn


def run_test() -> None:
    logging.basicConfig(level=logging.INFO)
    db_path = "test_memory.db"

    # Setup
    if os.path.exists(db_path):
        os.remove(db_path)
    setup_conn = setup_test_db(db_path)
    setup_conn.close()

    print("Initial Data:")
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, importance_score FROM memories").fetchall()
    for row in rows:
        print(f"  {row[0]}: {row[1]}")
    conn.close()

    # Run Worker
    print("\nRunning Scorer...")
    worker = ImportanceScorerWorker()
    worker.db_path = db_path  # Override DB path
    result = worker.process()
    print(f"Result: {result}")

    # Verify
    print("\nFinal Data:")
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, importance_score FROM memories").fetchall()
    for row in rows:
        print(f"  {row[0]}: {row[1]}")

    # specific checks
    scores = dict(rows)
    assert scores["mem_2"] > scores["mem_1"], "Important/active memory should score higher"
    assert scores["mem_3"] < 0.5, "Old inactive memory should score low"

    conn.close()
    print("\nTest Passed!")

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


if __name__ == "__main__":
    run_test()
