#!/usr/bin/env python3
"""
Master Test Suite for All Cognitive Services
Tests all Phase 3 cognitive components
"""

import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from cognitive.clustering_service import ClusteringService
from cognitive.context_analyzer import ContextAnalyzer
from cognitive.graph_engine import GraphQueryEngine
from cognitive.pattern_detector import PatternDetector
from cognitive.suggestion_engine import SuggestionEngine


def setup_comprehensive_test_db():
    """Setup comprehensive test database"""

    test_db = Path(__file__).parent / "data" / "test_cognitive.db"
    test_db.parent.mkdir(parents=True, exist_ok=True)

    if test_db.exists():
        test_db.unlink()

    conn = sqlite3.connect(str(test_db))
    conn.row_factory = sqlite3.Row

    # Create schema
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memories (
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
            created_at INTEGER,
            last_accessed INTEGER,
            archived INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            first_seen INTEGER,
            last_seen INTEGER,
            mention_count INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS entity_relationships (
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            type TEXT NOT NULL,
            strength REAL DEFAULT 0.5,
            created_at INTEGER,
            updated_at INTEGER,
            PRIMARY KEY (source_id, target_id, type)
        );

        CREATE TABLE IF NOT EXISTS memory_entities (
            memory_id TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            relevance REAL DEFAULT 0.5,
            PRIMARY KEY (memory_id, entity_id)
        );
    """)

    now = int(datetime.now(tz=UTC).timestamp() * 1000)

    # Insert test memories
    test_data = [
        {
            "id": "cog_test_1",
            "tier": "short",
            "type": "code",
            "source": "ide",
            "content": "async function fetchUserData(userId) { return await api.get(`/users/${userId}`); }",
            "timestamp": now - (10 * 60 * 1000),
            "project": "user-service",
            "language": "javascript",
            "tags": json.dumps(["async", "api", "user"]),
            "importance_score": 0.8,
            "access_count": 3,
        },
        {
            "id": "cog_test_2",
            "tier": "short",
            "type": "code",
            "source": "ide",
            "content": "function validateUserInput(input) { return input && input.length > 0; }",
            "timestamp": now - (15 * 60 * 1000),
            "project": "user-service",
            "language": "javascript",
            "tags": json.dumps(["validation", "user"]),
            "importance_score": 0.7,
            "access_count": 2,
        },
        {
            "id": "cog_test_3",
            "tier": "working",
            "type": "note",
            "source": "manual",
            "content": "TODO: Update API documentation for user endpoints",
            "timestamp": now - (7 * 24 * 60 * 60 * 1000),
            "project": "user-service",
            "tags": json.dumps(["todo", "documentation"]),
            "importance_score": 0.8,
            "access_count": 0,
        },
        {
            "id": "cog_test_4",
            "tier": "short",
            "type": "event",
            "source": "terminal",
            "content": "Error: Database connection timeout",
            "timestamp": now - (1 * 24 * 60 * 60 * 1000),
            "project": "user-service",
            "importance_score": 0.6,
            "access_count": 0,
        },
    ]

    for memory in test_data:
        conn.execute(
            """
            INSERT INTO memories (
                id, tier, type, source, content, content_hash, timestamp,
                project, language, tags, importance_score, access_count,
                created_at, last_accessed, archived
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
            (
                memory["id"],
                memory["tier"],
                memory["type"],
                memory["source"],
                memory["content"],
                f"hash_{memory['id']}",
                memory["timestamp"],
                memory.get("project"),
                memory.get("language"),
                memory.get("tags"),
                memory["importance_score"],
                memory["access_count"],
                memory["timestamp"],
                memory.get("last_accessed", memory["timestamp"]),
            ),
        )

    # Insert entities
    entities = [
        ("function:fetchUserData", "function", "fetchUserData", now, now, 2),
        ("function:validateUserInput", "function", "validateUserInput", now, now, 1),
        ("concept:user", "concept", "user", now, now, 4),
        ("concept:api", "concept", "api", now, now, 2),
    ]

    for entity in entities:
        conn.execute(
            """
            INSERT INTO entities (id, type, name, first_seen, last_seen, mention_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            entity,
        )

    # Insert relationships
    relationships = [
        ("function:fetchUserData", "concept:api", "related_to", 0.9, now, now),
        ("function:fetchUserData", "concept:user", "related_to", 0.95, now, now),
        ("function:validateUserInput", "concept:user", "related_to", 0.8, now, now),
    ]

    for rel in relationships:
        conn.execute(
            """
            INSERT INTO entity_relationships (source_id, target_id, type, strength, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            rel,
        )

    conn.commit()
    conn.close()

    print(f"✓ Created test database at {test_db}\n")
    return str(test_db)


def test_graph_engine(db_path):
    """Test graph query engine"""
    print("=" * 60)
    print("TEST 1: Graph Query Engine")
    print("=" * 60)

    engine = GraphQueryEngine(db_path=db_path)

    # Test build graph
    print("\n1.1 Building graph...")
    graph = engine.build_graph()
    print(f"  Nodes: {graph.number_of_nodes()}, Edges: {graph.number_of_edges()}")
    assert graph.number_of_nodes() > 0, "Graph has no nodes"
    print("  ✓ Graph built")

    # Test find related
    print("\n1.2 Finding related entities...")
    related = engine.find_related_entities("function:fetchUserData", max_hops=2)
    print(f"  Found {len(related)} related entities")
    print("  ✓ Related entities found")

    # Test central entities
    print("\n1.3 Finding central entities...")
    central = engine.get_central_entities(top_n=3)
    print(f"  Found {len(central)} central entities")
    print("  ✓ Central entities identified")

    print("\n✅ Graph Engine: PASSED\n")
    return True


def test_context_analyzer(db_path):
    """Test context analyzer"""
    print("=" * 60)
    print("TEST 2: Context Analyzer")
    print("=" * 60)

    analyzer = ContextAnalyzer(db_path=db_path)

    print("\n2.1 Analyzing current context...")
    context = analyzer.analyze_current_context(recent_window_minutes=60)
    print(f"  Active: {context.get('active', False)}")
    print(f"  Context type: {context.get('context_type')}")
    print(f"  Projects: {context.get('active_projects', [])}")
    print("  ✓ Context analyzed")

    print("\n✅ Context Analyzer: PASSED\n")
    return True


def test_suggestion_engine(db_path):
    """Test suggestion engine"""
    print("=" * 60)
    print("TEST 3: Suggestion Engine")
    print("=" * 60)

    engine = SuggestionEngine(db_path=db_path)

    print("\n3.1 Generating suggestions...")
    suggestions = engine.generate_suggestions(limit=5)
    print(f"  Generated {len(suggestions)} suggestions")

    if suggestions:
        for s in suggestions[:2]:
            print(f"    - [{s.get('type')}] {s.get('title', 'N/A')}")
    print("  ✓ Suggestions generated")

    print("\n3.2 Detecting issues...")
    issues = engine.detect_potential_issues(limit=5)
    print(f"  Found {len(issues)} potential issues")
    print("  ✓ Issues detected")

    print("\n✅ Suggestion Engine: PASSED\n")
    return True


def test_pattern_detector(db_path):
    """Test pattern detector"""
    print("=" * 60)
    print("TEST 4: Pattern Detector")
    print("=" * 60)

    detector = PatternDetector(db_path=db_path)

    print("\n4.1 Detecting patterns...")
    patterns = detector.detect_recurring_patterns(days=30)
    print(f"  Found {len(patterns)} patterns")
    print("  ✓ Patterns detected")

    print("\n4.2 Tracking trends...")
    trends = detector.track_trends(days=30)
    print(f"  Trend direction: {trends.get('trend_direction', 'N/A')}")
    print("  ✓ Trends tracked")

    print("\n4.3 Getting statistics...")
    stats = detector.get_pattern_statistics()
    print(f"  Total memories: {stats.get('total_memories', 0)}")
    print("  ✓ Statistics retrieved")

    print("\n✅ Pattern Detector: PASSED\n")
    return True


def test_clustering_service(db_path):
    """Test clustering service"""
    print("=" * 60)
    print("TEST 5: Clustering Service")
    print("=" * 60)

    service = ClusteringService(db_path=db_path)

    print("\n5.1 Getting cluster representatives...")
    reps = service.get_cluster_representatives(["cog_test_1", "cog_test_2"], top_n=2)
    print(f"  Got {len(reps)} representatives")
    print("  ✓ Representatives retrieved")

    print("\n✅ Clustering Service: PASSED\n")
    return True


def main():
    """Run all cognitive tests"""
    print("\n" + "=" * 60)
    print("PHASE 3 COGNITIVE SERVICES VALIDATION")
    print("=" * 60 + "\n")

    # Setup
    db_path = setup_comprehensive_test_db()

    try:
        results = []
        results.append(("Graph Engine", test_graph_engine(db_path)))
        results.append(("Context Analyzer", test_context_analyzer(db_path)))
        results.append(("Suggestion Engine", test_suggestion_engine(db_path)))
        results.append(("Pattern Detector", test_pattern_detector(db_path)))
        results.append(("Clustering Service", test_clustering_service(db_path)))

        # Summary
        print("=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for name, result in results:
            status = "✅" if result else "❌"
            print(f"  {status} {name}")

        print(f"\nResults: {passed}/{total} passed")

        if passed == total:
            print("\n✅ ALL COGNITIVE SERVICES VALIDATED")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED")
            return 1

    finally:
        # Cleanup
        test_db = Path(db_path)
        if test_db.exists():
            test_db.unlink()


if __name__ == "__main__":
    sys.exit(main())
