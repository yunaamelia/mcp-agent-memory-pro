import os
import sqlite3
import sys
import unittest
from datetime import UTC, datetime

# Add python directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../python")))

from analytics.dashboard_service import DashboardService


class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.service = DashboardService(self.conn)
        self._setup_db()

    def _setup_db(self):
        self.conn.execute("""
            CREATE TABLE memories (
                id TEXT PRIMARY KEY,
                content TEXT,
                type TEXT,
                tier TEXT,
                project TEXT,
                importance_score REAL,
                access_count INTEGER DEFAULT 0,
                timestamp INTEGER,
                entities TEXT,
                archived INTEGER DEFAULT 0
            )
        """)

        self.conn.execute("""
            CREATE TABLE entities (
                name TEXT,
                type TEXT,
                mention_count INTEGER
            )
        """)

        self.conn.execute("""
            CREATE TABLE entity_relationships (
                source TEXT,
                target TEXT,
                type TEXT
            )
        """)

        # Add sample data
        now = int(datetime.now(UTC).timestamp() * 1000)
        day = 24 * 60 * 60 * 1000

        memories = [
            # id, content, type, tier, project, importance, access, timestamp, entities, archived
            ("1", "Important task", "task", "core", "proj1", 0.9, 5, now, '["ent1"]', 0),
            ("2", "Notes", "note", "short", "proj1", 0.3, 1, now - day, '["ent1"]', 0),
            ("3", "Old stuff", "archive", "long", "proj2", 0.1, 0, now - 10 * day, "[]", 0),
            ("4", "Archived item", "task", "core", "proj1", 0.5, 2, now - day, "[]", 1),
        ]

        self.conn.executemany(
            "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", memories
        )

        entities = [("ent1", "concept", 10), ("ent2", "person", 5)]

        self.conn.executemany("INSERT INTO entities VALUES (?, ?, ?)", entities)

        self.conn.commit()

    def test_get_overview(self):
        stats = self.service.get_overview()
        self.assertEqual(stats["total_memories"], 3)  # Excludes archived
        self.assertEqual(stats["by_tier"]["core"], 1)
        self.assertEqual(stats["by_type"]["task"], 1)
        self.assertGreater(stats["avg_importance"], 0)
        self.assertEqual(stats["most_active_project"], "proj1")

    def test_project_breakdown(self):
        projects = self.service.get_project_breakdown()
        p1 = next(p for p in projects if p["project"] == "proj1")
        self.assertEqual(p1["memory_count"], 2)
        self.assertEqual(p1["total_accesses"], 6)

    def test_health_metrics(self):
        metrics = self.service.get_health_metrics()
        # Just verify structure and basic calculation hasn't crashed
        self.assertIn("health_score", metrics)
        self.assertTrue(0 <= metrics["health_score"] <= 100)


if __name__ == "__main__":
    unittest.main()
