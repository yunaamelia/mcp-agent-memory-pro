"""
Tests for Suggestion Engine
"""

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
    """Create a test database with sample data"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

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
            tags TEXT,
            entities TEXT,
            importance_score REAL DEFAULT 0.5,
            access_count INTEGER DEFAULT 0,
            last_accessed INTEGER,
            created_at INTEGER,
            archived INTEGER DEFAULT 0
        )
    """)

    now = int(time.time() * 1000)

    # High importance but forgotten memory
    conn.execute(
        """
        INSERT INTO memories (id, type, source, content, content_hash, timestamp, project, importance_score, last_accessed, archived)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """,
        (
            "forgotten1",
            "decision",
            "agent",
            "Important security decision about auth",
            "hash1",
            now - 86400000 * 30,
            "test-project",
            0.9,
            now - 86400000 * 20,
        ),
    )

    # TODO item
    conn.execute(
        """
        INSERT INTO memories (id, type, source, content, content_hash, timestamp, project, importance_score, archived)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """,
        (
            "todo1",
            "code",
            "agent",
            "// TODO: Implement error handling\nfunction handleError() {}",
            "hash2",
            now - 3600000,
            "test-project",
            0.5,
        ),
    )

    # Repeated error
    for i in range(3):
        conn.execute(
            """
            INSERT INTO memories (id, type, source, content, content_hash, timestamp, project, importance_score, archived)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
            (
                f"error{i}",
                "command",
                "terminal",
                "Error: Connection refused to database",
                "error_hash",
                now - 3600000 * i,
                "test-project",
                0.4,
            ),
        )

    # Best practice insight
    conn.execute(
        """
        INSERT INTO memories (id, type, source, content, content_hash, timestamp, project, importance_score, archived)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """,
        (
            "insight1",
            "insight",
            "agent",
            "Always use parameterized queries to prevent SQL injection",
            "hash3",
            now - 86400000 * 5,
            "test-project",
            0.85,
        ),
    )

    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


class TestSuggestionEngine:
    """Test cases for SuggestionEngine"""

    def test_generate_suggestions(self, test_db):
        """Test suggestion generation"""
        from cognitive.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(db_path=test_db)
        suggestions = engine.generate_suggestions(limit=5)

        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5

    def test_suggestions_have_required_fields(self, test_db):
        """Test that suggestions have required fields"""
        from cognitive.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(db_path=test_db)
        suggestions = engine.generate_suggestions(limit=5)

        for suggestion in suggestions:
            assert "type" in suggestion
            assert "title" in suggestion
            assert "priority" in suggestion

    def test_detect_potential_issues_todos(self, test_db):
        """Test detecting unresolved TODOs"""
        from cognitive.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(db_path=test_db)
        issues = engine.detect_potential_issues(project="test-project")

        todo_issues = [i for i in issues if i["type"] == "unresolved_todo"]
        assert len(todo_issues) > 0

    def test_detect_potential_issues_repeated_errors(self, test_db):
        """Test detecting repeated errors"""
        from cognitive.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(db_path=test_db)
        issues = engine.detect_potential_issues(project="test-project")

        error_issues = [i for i in issues if i["type"] == "repeated_error"]
        assert len(error_issues) > 0

    def test_surface_forgotten_knowledge(self, test_db):
        """Test surfacing forgotten but important memories"""
        from cognitive.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(db_path=test_db)
        forgotten = engine.surface_forgotten_knowledge(days_threshold=14, limit=5)

        assert len(forgotten) > 0
        assert all("memory_id" in f for f in forgotten)
        assert all("days_since_access" in f for f in forgotten)

    def test_forgotten_knowledge_filtered_by_importance(self, test_db):
        """Test that only important memories are surfaced"""
        from cognitive.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(db_path=test_db)
        forgotten = engine.surface_forgotten_knowledge(days_threshold=14, limit=10)

        for item in forgotten:
            assert item["importance_score"] >= 0.6

    def test_recommend_best_practices(self, test_db):
        """Test best practice recommendations"""
        from cognitive.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(db_path=test_db)
        # Method signature: recommend_best_practices(context=None, limit=3)
        context = {"primary_project": "test-project", "context_type": "coding"}
        practices = engine.recommend_best_practices(context=context, limit=5)

        assert isinstance(practices, list)


class TestSuggestionEngineWithContext:
    """Test SuggestionEngine with context"""

    def test_suggestions_with_context(self, test_db):
        """Test suggestions consider context"""
        from cognitive.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(db_path=test_db)

        context = {
            "active": True,
            "context_type": "debugging",
            "active_projects": ["test-project"],
            "active_entities": ["database", "connection"],
            "time_window_minutes": 30,
        }

        suggestions = engine.generate_suggestions(context=context, limit=5)

        assert len(suggestions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
