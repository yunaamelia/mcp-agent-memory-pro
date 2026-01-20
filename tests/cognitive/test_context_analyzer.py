"""
Tests for Context Analyzer
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
    """Create a test database with sample memories"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    # Create memories table
    conn.execute("""
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
            language TEXT,
            tags TEXT,
            entities TEXT,
            importance_score REAL DEFAULT 0.5,
            access_count INTEGER DEFAULT 0,
            last_accessed INTEGER,
            created_at INTEGER,
            promoted_from TEXT,
            archived INTEGER DEFAULT 0
        )
    """)

    # Insert recent memories (within 30 min window)
    now = int(time.time() * 1000)
    recent_memories = [
        (
            "m1",
            "code",
            "agent",
            "Implementing auth handler",
            now - 60000,
            "mcp-memory",
            "/src/auth.ts",
            json.dumps(["handleAuth", "UserService", "validateToken"]),
            0.7,
        ),
        (
            "m2",
            "code",
            "agent",
            "Adding user validation",
            now - 120000,
            "mcp-memory",
            "/src/user.ts",
            json.dumps(["UserService", "createUser"]),
            0.6,
        ),
        (
            "m3",
            "command",
            "terminal",
            "npm test",
            now - 180000,
            "mcp-memory",
            None,
            json.dumps(["test"]),
            0.4,
        ),
    ]

    for mid, mtype, source, content, ts, project, fpath, entities, importance in recent_memories:
        conn.execute(
            """
            INSERT INTO memories (id, type, source, content, timestamp, project, file_path, entities, importance_score, archived)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
            (mid, mtype, source, content, ts, project, fpath, entities, importance),
        )

    # Insert older memories (for recall)
    older_memories = [
        (
            "m4",
            "decision",
            "agent",
            "Decided to use JWT for auth",
            now - 3600000 * 24,
            "mcp-memory",
            None,
            json.dumps(["handleAuth", "JWT", "auth"]),
            0.9,
        ),
        (
            "m5",
            "insight",
            "agent",
            "UserService should validate input",
            now - 3600000 * 48,
            "mcp-memory",
            None,
            json.dumps(["UserService", "validation"]),
            0.8,
        ),
    ]

    for mid, mtype, source, content, ts, project, fpath, entities, importance in older_memories:
        conn.execute(
            """
            INSERT INTO memories (id, type, source, content, timestamp, project, file_path, entities, importance_score, archived)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
            (mid, mtype, source, content, ts, project, fpath, entities, importance),
        )

    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


class TestContextAnalyzer:
    """Test cases for ContextAnalyzer"""

    def test_analyze_current_context_active(self, test_db):
        """Test context analysis with recent activity"""
        from cognitive.context_analyzer import ContextAnalyzer

        analyzer = ContextAnalyzer(db_path=test_db)
        context = analyzer.analyze_current_context(recent_window_minutes=30)

        assert context["active"] is True
        assert context["recent_activity_count"] > 0
        assert "mcp-memory" in context["active_projects"]

    def test_analyze_current_context_inactive(self, test_db):
        """Test context analysis with no recent activity"""
        from cognitive.context_analyzer import ContextAnalyzer

        # Set very short window
        analyzer = ContextAnalyzer(db_path=test_db)
        context = analyzer.analyze_current_context(recent_window_minutes=0)

        assert context["active"] is False
        assert context["recent_activity_count"] == 0

    def test_analyze_context_with_project_hint(self, test_db):
        """Test context analysis with project filter"""
        from cognitive.context_analyzer import ContextAnalyzer

        analyzer = ContextAnalyzer(db_path=test_db)
        context = analyzer.analyze_current_context(
            recent_window_minutes=30, project_hint="mcp-memory"
        )

        assert context["active"] is True
        assert context["primary_project"] == "mcp-memory"

    def test_context_type_inference(self, test_db):
        """Test context type is inferred"""
        from cognitive.context_analyzer import ContextAnalyzer

        analyzer = ContextAnalyzer(db_path=test_db)
        context = analyzer.analyze_current_context(recent_window_minutes=30)

        assert context["context_type"] is not None
        assert context["context_type"] in [
            "coding",
            "debugging",
            "planning",
            "documentation",
            "system_admin",
            "general",
            "analysis",
        ]

    def test_active_entities_extraction(self, test_db):
        """Test that entities are extracted from recent memories"""
        from cognitive.context_analyzer import ContextAnalyzer

        analyzer = ContextAnalyzer(db_path=test_db)
        context = analyzer.analyze_current_context(recent_window_minutes=30)

        assert len(context["active_entities"]) > 0
        assert "UserService" in context["active_entities"]

    def test_recall_relevant_memories(self, test_db):
        """Test recalling relevant memories based on context"""
        from cognitive.context_analyzer import ContextAnalyzer

        analyzer = ContextAnalyzer(db_path=test_db)
        context = analyzer.analyze_current_context(recent_window_minutes=30)

        recalled = analyzer.recall_relevant_memories(context=context, limit=5)

        assert len(recalled) > 0
        assert all("relevance_score" in m for m in recalled)
        assert all("recall_reason" in m for m in recalled)

    def test_recall_memories_sorted_by_relevance(self, test_db):
        """Test that recalled memories are sorted by relevance"""
        from cognitive.context_analyzer import ContextAnalyzer

        analyzer = ContextAnalyzer(db_path=test_db)
        context = analyzer.analyze_current_context(recent_window_minutes=30)

        recalled = analyzer.recall_relevant_memories(context=context, limit=5)

        if len(recalled) >= 2:
            scores = [m["relevance_score"] for m in recalled]
            assert scores == sorted(scores, reverse=True)

    def test_recall_excludes_recent(self, test_db):
        """Test that recent memories are excluded from recall"""
        from cognitive.context_analyzer import ContextAnalyzer

        analyzer = ContextAnalyzer(db_path=test_db)
        context = analyzer.analyze_current_context(recent_window_minutes=30)

        recalled = analyzer.recall_relevant_memories(
            context=context, limit=10, exclude_recent_minutes=30
        )

        # Recent memory IDs should not be in recalled
        recent_ids = ["m1", "m2", "m3"]
        recalled_ids = [m["id"] for m in recalled]

        for rid in recent_ids:
            assert rid not in recalled_ids

    def test_get_related_memories_for_entity(self, test_db):
        """Test getting memories related to specific entity"""
        from cognitive.context_analyzer import ContextAnalyzer

        analyzer = ContextAnalyzer(db_path=test_db)

        memories = analyzer.get_related_memories_for_entity("UserService", limit=5)

        assert len(memories) > 0
        # All should contain the entity
        for m in memories:
            assert "UserService" in m.get("entities", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
