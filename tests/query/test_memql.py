import os
import sqlite3
import sys
import unittest

# Add python directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../python")))

from query.memql_executor import MemQLExecutor
from query.memql_parser import MemQLParser


class TestMemQL(unittest.TestCase):
    def setUp(self):
        self.parser = MemQLParser()
        self.conn = sqlite3.connect(":memory:")
        self.executor = MemQLExecutor(self.conn)
        self._setup_db()

    def _setup_db(self):
        self.conn.execute("""
            CREATE TABLE memories (
                id TEXT PRIMARY KEY,
                content TEXT,
                type TEXT,
                project TEXT,
                importance_score REAL,
                archived INTEGER DEFAULT 0
            )
        """)

        data = [
            ("1", "Fix bug in auth", "task", "auth-service", 0.8, 0),
            ("2", "API design docs", "document", "api-gateway", 0.5, 0),
            ("3", "Refactor database", "task", "core", 0.9, 0),
            ("4", "Meeting notes", "note", "general", 0.2, 0),
            ("5", "Old archive", "archive", "legacy", 0.1, 1),
        ]

        self.conn.executemany("INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def test_parser_simple(self):
        query = "SELECT * FROM memories"
        parsed = self.parser.parse(query)
        self.assertEqual(parsed["select"], ["*"])
        self.assertEqual(parsed["from"], "memories")
        self.assertIsNone(parsed["where"])

    def test_parser_where(self):
        query = "SELECT content FROM memories WHERE type = 'task'"
        parsed = self.parser.parse(query)
        self.assertEqual(parsed["where"]["field"], "type")
        self.assertEqual(parsed["where"]["value"], "task")

    def test_parser_complex_where(self):
        query = "SELECT * FROM memories WHERE type = 'task' AND importance_score > 0.5"
        parsed = self.parser.parse(query)
        self.assertEqual(len(parsed["where"]["conditions"]), 2)
        self.assertEqual(parsed["where"]["operators"], ["AND"])

    def test_executor_select_all(self):
        result = self.executor.execute("SELECT * FROM memories")
        self.assertEqual(result["count"], 5)

    def test_executor_filter(self):
        result = self.executor.execute("SELECT * FROM memories WHERE type = 'task'")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["results"][0]["type"], "task")

    def test_executor_ordering(self):
        result = self.executor.execute("SELECT * FROM memories ORDER BY importance_score DESC")
        self.assertEqual(result["results"][0]["id"], "3")  # 0.9 importance
        self.assertEqual(result["results"][-1]["id"], "5")  # 0.1 importance

    def test_executor_limit(self):
        result = self.executor.execute("SELECT * FROM memories LIMIT 2")
        self.assertEqual(result["count"], 2)

    def test_executor_like(self):
        result = self.executor.execute("SELECT * FROM memories WHERE content LIKE '%bug%'")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "1")


if __name__ == "__main__":
    unittest.main()
