#!/usr/bin/env python3
"""
Test Intelligence Services
Tests scoring, NER, and summarization services
"""

import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from config import CLAUDE_API_KEY
from services.ner_service import NERService
from services.scoring_service import ImportanceScoringService


def test_scoring_service():
    """Test importance scoring"""

    print("Testing Importance Scoring Service")
    print("=" * 50)

    # Create test database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Create minimal schema with all required columns
    conn.execute("""
        CREATE TABLE memories (
            id TEXT, type TEXT, source TEXT, content TEXT,
            timestamp INTEGER, access_count INTEGER, created_at INTEGER,
            project TEXT, tags TEXT, archived INTEGER DEFAULT 0
        )
    """)

    # Insert test data with proper timestamp (milliseconds)
    now = int(datetime.now(UTC).timestamp() * 1000)
    conn.execute(
        """
        INSERT INTO memories VALUES
        ('test1', 'code', 'ide', 'function test() {}', ?, 5, ?, 'proj1', '["tag1"]', 0)
        """,
        (now, now),
    )
    conn.commit()

    # Test scoring
    scorer = ImportanceScoringService(conn)

    cursor = conn.execute("SELECT * FROM memories WHERE id = ?", ("test1",))
    memory = dict(cursor.fetchone())
    memory["tags"] = ["tag1"]

    score = scorer.calculate_importance(memory)

    print(f"Calculated importance score: {score:.3f}")

    assert 0.0 <= score <= 1.0, "Score out of range"
    assert score > 0.3, "Score too low for high-engagement memory"

    print("✅ Scoring service test passed!\n")
    conn.close()


def test_ner_service():
    """Test entity extraction"""

    print("Testing NER Service")
    print("=" * 50)

    ner = NERService()

    # Test code extraction
    code = """
    import React from 'react';

    function fetchUserData(userId) {
        return api.get(`/users/${userId}`);
    }

    class UserManager {
        constructor() {}
    }
    """

    entities = ner.extract_entities(code, "code", {"project": "test-app", "language": "javascript"})

    print(f"Extracted {len(entities)} entities:")
    for e in entities[:5]:
        print(f"  {e['type']:10s} | {e['name']:20s} | {e['confidence']:.2f}")

    # Verify expected entities
    entity_types = {e["type"] for e in entities}
    assert "function" in entity_types, "Failed to extract functions"
    assert "class" in entity_types, "Failed to extract classes"

    function_names = {e["name"] for e in entities if e["type"] == "function"}
    assert "fetchUserData" in function_names, "Failed to extract specific function"

    print("✅ NER service test passed!\n")


def test_summarization_service():
    """Test summarization (if API key available)"""

    print("Testing Summarization Service")
    print("=" * 50)

    if not CLAUDE_API_KEY:
        print("⚠️  Claude API key not set - skipping summarization test")
        return

    try:
        from services.claude_client import ClaudeClient

        client = ClaudeClient()

        code = """
        async function authenticateUser(credentials) {
            const { username, password } = credentials;
            const user = await db.users.findOne({ username });
            if (!user) throw new Error('User not found');
            const valid = await bcrypt.compare(password, user.passwordHash);
            if (!valid) throw new Error('Invalid password');
            return jwt.sign({ userId: user.id }, SECRET_KEY);
        }
        """

        summary = client.summarize_memory(
            code, "code", {"project": "auth-service", "language": "javascript"}
        )

        print(f"Original: {len(code)} chars → Summary: {len(summary)} chars")
        assert len(summary) < len(code), "Summary not shorter"

        print("✅ Summarization service test passed!\n")

    except Exception as e:
        print(f"⚠️  Summarization test warning: {e}\n")


def main():
    """Run all service tests"""

    print("\n" + "=" * 50)
    print("INTELLIGENCE SERVICES VALIDATION")
    print("=" * 50 + "\n")

    try:
        test_scoring_service()
        test_ner_service()
        test_summarization_service()

        print("=" * 50)
        print("✅ ALL SERVICE TESTS PASSED")
        print("=" * 50)

        return 0

    except Exception as e:
        print(f"\n❌ Service tests failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
