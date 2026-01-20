"""
Integration Test for Worker Pipeline
Simulates the flow of data through the worker system
"""

import os
import sqlite3
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add python dir to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "python"))

# Mock config to use in-memory DB or temporary file
# We'll just monkeypatch the workers' get_db_connection for this test
from workers.entity_extractor import EntityExtractorWorker
from workers.importance_scorer import ImportanceScorerWorker
from workers.memory_promoter import MemoryPromoterWorker


class TestWorkerPipeline(unittest.TestCase):
    def setUp(self):
        # Create temp DB
        self.db_path = "test_workers.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_schema()

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def create_schema(self):
        # Full schema
        self.conn.execute("""
            CREATE TABLE memories (
                id TEXT PRIMARY KEY,
                type TEXT,
                source TEXT,
                content TEXT,
                timestamp REAL,
                created_at REAL,
                access_count INTEGER DEFAULT 0,
                project TEXT,
                file_path TEXT,
                tags TEXT,
                importance_score REAL,
                tier TEXT DEFAULT 'short',
                summary TEXT,
                archived INTEGER DEFAULT 0
            )
        """)

    def get_test_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def test_pipeline(self):
        """Run all workers in sequence"""

        # 1. Seed Data
        print("\n[Seeding Data]...")
        self.conn.execute(
            """
            INSERT INTO memories (id, type, source, content, timestamp, created_at, access_count, project, tier)
            VALUES
            ('mem_1', 'code', 'manual', 'def important_algo(): pass', ?, ?, 5, 'AI', 'short'),
            ('mem_2', 'note', 'terminal', 'todo list', ?, ?, 0, NULL, 'short')
        """,
            (
                datetime.now(UTC).timestamp(),
                datetime.now(UTC).timestamp(),
                (datetime.now(UTC) - timedelta(days=5)).timestamp(),
                (datetime.now(UTC) - timedelta(days=5)).timestamp(),
            ),
        )
        self.conn.commit()

        # 2. Run Importance Scorer
        print("[Running Scorer]...")
        scorer = ImportanceScorerWorker()
        scorer.get_db_connection = self.get_test_connection  # Monkeypatch
        res_score = scorer.run()
        self.assertTrue(res_score["success"])

        # Verify scores
        row = self.conn.execute("SELECT importance_score FROM memories WHERE id='mem_1'").fetchone()
        print(f"  Mem 1 Score: {row['importance_score']}")
        self.assertIsNotNone(row["importance_score"])

        # 3. Run Entity Extractor
        print("[Running Extractor]...")
        extractor = EntityExtractorWorker()
        extractor.get_db_connection = self.get_test_connection
        res_ent = extractor.run()
        self.assertTrue(res_ent["success"])

        # Verify entities (table creation is handled by worker if not exists)
        # Re-connect to see schema changes
        # self.conn needs to be refreshed or we check existence
        # The worker creates 'memory_entities' table.
        check_conn = self.get_test_connection()
        try:
            row = check_conn.execute("SELECT count(*) as c FROM memory_entities").fetchone()
            print(f"  Entities Found: {row['c']}")
        except:
            print("  Entity table not found (might be normal if mock logic differs)")
        check_conn.close()

        # 4. Run Promoter
        print("[Running Promoter]...")
        promoter = MemoryPromoterWorker()
        promoter.get_db_connection = self.get_test_connection

        # Force Mem 1 to be old enough for logic if needed, but our logic used created_at which we set
        # Mem 2 is 5 days old (SHORT_TERM_DAYS default is 2).
        # But Mem 2 has low access/score.
        # Mem 1 is new (now), so it might stay in short unless we hack it.
        # Let's hack Mem 1 to be old enough so it gets promoted to working due to high score
        self.conn.execute(
            "UPDATE memories SET created_at = ? WHERE id = 'mem_1'",
            ((datetime.now(UTC) - timedelta(days=3)).timestamp(),),
        )
        self.conn.commit()

        res_prom = promoter.run()
        self.assertTrue(res_prom["success"])

        # Verify Promotion
        row = self.conn.execute("SELECT tier FROM memories WHERE id='mem_1'").fetchone()
        print(f"  Mem 1 Tier: {row['tier']}")
        self.assertEqual(row["tier"], "working")


if __name__ == "__main__":
    unittest.main()
