"""
Tests for Pattern Detector
"""

import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))


@pytest.fixture
def test_db():
    """Create a test database with pattern data"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            tier TEXT DEFAULT 'short',
            type TEXT NOT NULL,
            source TEXT NOT NULL,
            content TEXT NOT NULL,
            content_hash TEXT,
            timestamp INTEGER NOT NULL,
            project TEXT,
            file_path TEXT,
            entities TEXT,
            importance_score REAL DEFAULT 0.5,
            access_count INTEGER DEFAULT 0,
            archived INTEGER DEFAULT 0
        );

        CREATE TABLE entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            mention_count INTEGER DEFAULT 1
        );

        CREATE TABLE entity_relationships (
            source_id TEXT,
            target_id TEXT,
            type TEXT,
            strength REAL DEFAULT 0.5
        );
    """)

    now = int(time.time() * 1000)

    # Create memories with patterns
    for i in range(20):
        # Alternate between projects
        project = "project-a" if i % 2 == 0 else "project-b"
        mtype = "code" if i % 3 == 0 else ("command" if i % 3 == 1 else "note")
        entities = (
            json.dumps(["entity1", "entity2"]) if i % 2 == 0 else json.dumps(["entity2", "entity3"])
        )

        conn.execute(
            """
            INSERT INTO memories (id, type, source, content, content_hash, timestamp, project, entities, importance_score, archived)
            VALUES (?, ?, 'test', ?, ?, ?, ?, ?, 0.5, 0)
        """,
            (
                f"m{i}",
                mtype,
                f"Memory content {i}",
                f"hash{i}",
                now - 3600000 * i,
                project,
                entities,
            ),
        )

    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


class TestPatternDetector:
    """Test cases for PatternDetector"""

    def test_detect_recurring_patterns(self, test_db):
        """Test detecting recurring patterns"""
        from cognitive.pattern_detector import PatternDetector

        detector = PatternDetector(db_path=test_db)
        patterns = detector.detect_recurring_patterns(days=30, min_occurrences=2)

        assert isinstance(patterns, list)

    def test_pattern_has_required_fields(self, test_db):
        """Test patterns have required fields"""
        from cognitive.pattern_detector import PatternDetector

        detector = PatternDetector(db_path=test_db)
        patterns = detector.detect_recurring_patterns(days=30, min_occurrences=2)

        for pattern in patterns:
            assert "type" in pattern
            assert "frequency" in pattern
            assert "description" in pattern

    def test_identify_anomalies(self, test_db):
        """Test anomaly identification"""
        from cognitive.pattern_detector import PatternDetector

        detector = PatternDetector(db_path=test_db)
        anomalies = detector.identify_anomalies(days=7)

        assert isinstance(anomalies, list)

    def test_track_trends(self, test_db):
        """Test trend tracking"""
        from cognitive.pattern_detector import PatternDetector

        detector = PatternDetector(db_path=test_db)
        trend = detector.track_trends(days=30)

        assert "trend_direction" in trend
        assert "trend_ratio" in trend
        assert "period_counts" in trend
        assert trend["trend_direction"] in [
            "increasing",
            "decreasing",
            "stable",
            "insufficient_data",
        ]

    def test_track_trends_for_project(self, test_db):
        """Test trend tracking for specific project"""
        from cognitive.pattern_detector import PatternDetector

        detector = PatternDetector(db_path=test_db)
        trend = detector.track_trends(project="project-a", days=30)

        assert trend["project"] == "project-a"
        assert "trend_direction" in trend

    def test_get_pattern_statistics(self, test_db):
        """Test getting pattern statistics"""
        from cognitive.pattern_detector import PatternDetector

        detector = PatternDetector(db_path=test_db)
        stats = detector.get_pattern_statistics()

        assert "total_memories" in stats
        assert "memories_by_type" in stats
        assert stats["total_memories"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
