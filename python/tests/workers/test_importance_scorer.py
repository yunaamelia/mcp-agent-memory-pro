"""
Test Importance Scorer
"""

import sqlite3
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

# Add python dir to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "python"))

from services.scoring_service import ImportanceScoringService


class TestImportanceScorer(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.create_schema()
        self.service = ImportanceScoringService(self.conn)

    def create_schema(self):
        self.conn.execute("""
            CREATE TABLE memories (
                id TEXT PRIMARY KEY,
                type TEXT,
                source TEXT,
                content TEXT,
                timestamp REAL,
                created_at REAL,
                access_count INTEGER,
                project TEXT,
                file_path TEXT,
                tags TEXT,
                importance_score REAL,
                archived INTEGER DEFAULT 0
            )
        """)

    def test_calculate_importance_high(self):
        """Test calculation for a high importance memory"""
        memory = {
            "content": "def critical_function(): pass",
            "type": "code",
            "source": "manual",
            "access_count": 10,
            "created_at": datetime.now(UTC).timestamp(),
            "timestamp": datetime.now(UTC).timestamp(),
            "project": "core_system",
            "file_path": "/src/core.py",
            "tags": ["critical", "core"],
        }

        score = self.service.calculate_importance(memory)
        self.assertGreater(score, 0.7)

    def test_calculate_importance_low(self):
        """Test calculation for a low importance memory"""
        memory = {
            "content": "ls -la",
            "type": "command",
            "source": "terminal",
            "access_count": 0,
            "created_at": datetime.now(UTC).timestamp() - 86400 * 30,  # Old
            "timestamp": datetime.now(UTC).timestamp() - 86400 * 30,
            "project": None,
            "file_path": None,
            "tags": [],
        }

        score = self.service.calculate_importance(memory)
        self.assertLess(score, 0.6)

    def tearDown(self):
        self.conn.close()


if __name__ == "__main__":
    unittest.main()
