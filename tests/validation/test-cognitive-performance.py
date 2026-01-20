#!/usr/bin/env python3
"""
Cognitive Performance Benchmarks
Tests performance of Phase 3 cognitive features
"""

import json
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from cognitive.clustering_service import ClusteringService
from cognitive.context_analyzer import ContextAnalyzer
from cognitive.graph_engine import GraphQueryEngine
from cognitive.pattern_detector import PatternDetector
from cognitive.suggestion_engine import SuggestionEngine


def setup_performance_test_db(num_memories=200):
    """Create test database with many memories for performance testing"""

    test_db = Path(__file__).parent.parent / "data" / "test_perf_cognitive.db"
    test_db.parent.mkdir(parents=True, exist_ok=True)

    if test_db.exists():
        test_db.unlink()

    conn = sqlite3.connect(str(test_db))
    conn.row_factory = sqlite3.Row

    # Create schema using execute for simpler setup in test
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
    """)

    print(f"Creating {num_memories} test memories...")

    now = int(datetime.now(UTC).timestamp() * 1000)
    projects = ["proj-a", "proj-b", "proj-c"]
    types = ["code", "note", "command", "event"]

    # Insert memories
    for i in range(num_memories):
        conn.execute(
            """
            INSERT INTO memories (
                id, tier, type, source, content, content_hash, timestamp,
                project, language, tags, importance_score, access_count,
                created_at, last_accessed, archived
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
            (
                f"perf_cog_{i}",
                "short" if i % 3 == 0 else "working",
                types[i % len(types)],
                "ide",
                f"function test{i}() {{ return {i}; }}",
                f"hash_{i}",
                now - (i * 60000),  # Spread over time
                projects[i % len(projects)],
                "javascript",
                json.dumps(["tag1", "tag2"]),
                0.5 + (i % 5) * 0.1,
                i % 10,
                now - (i * 60000),
                now - (i * 30000),
            ),
        )

    # Insert entities
    for i in range(50):
        conn.execute(
            """
            INSERT INTO entities (id, type, name, first_seen, last_seen, mention_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                f"entity_{i}",
                "function" if i % 2 == 0 else "concept",
                f"entity_{i}",
                int(datetime.now(UTC).timestamp()),
                int(datetime.now(UTC).timestamp()),
                i % 10,
            ),
        )

    # Insert relationships
    for i in range(100):
        source = f"entity_{i % 50}"
        target = f"entity_{(i + 1) % 50}"
        conn.execute(
            """
            INSERT OR IGNORE INTO entity_relationships
            (source_id, target_id, type, strength, created_at, updated_at)
            VALUES (?, ?, 'related_to', ?, ?, ?)
        """,
            (
                source,
                target,
                0.5 + (i % 5) * 0.1,
                int(datetime.now(UTC).timestamp()),
                int(datetime.now(UTC).timestamp()),
            ),
        )

    conn.commit()
    conn.close()

    print("✓ Created test database\n")
    return str(test_db)


def benchmark_component(name, func, *args, target_time=None):
    """Benchmark a component"""

    print(f"Benchmarking {name}")
    print("-" * 60)

    # Warm-up if possible (some might be one-off)
    try:
        func(*args)
    except Exception as e:
        print(f"  Warm-up failed (might be ok): {e}")

    # Benchmark runs
    times = []
    for i in range(3):
        start = time.time()
        try:
            func(*args)
            duration = time.time() - start
            times.append(duration)
            print(f"  Run {i + 1}: {duration:.3f}s")
        except Exception as e:
            print(f"  Run {i + 1} failed: {e}")

    if not times:
        return {
            "component": name,
            "avg": 0,
            "min": 0,
            "max": 0,
            "target": target_time,
            "status": "fail",
        }

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\n  Average: {avg_time:.3f}s")
    print(f"  Min: {min_time:.3f}s")
    print(f"  Max: {max_time:.3f}s")

    if target_time:
        status = "✅" if avg_time < target_time else "⚠️"
        print(f"  Target: {target_time}s {status}")

    print()

    return {
        "component": name,
        "avg": avg_time,
        "min": min_time,
        "max": max_time,
        "target": target_time,
        "status": "pass" if not target_time or avg_time < target_time else "warn",
    }


def main():
    """Run performance benchmarks"""

    print("\n" + "=" * 60)
    print("COGNITIVE PERFORMANCE BENCHMARKS")
    print("=" * 60 + "\n")

    # Setup
    db_path = setup_performance_test_db(200)

    # We need to pass db_path to initializers as implemented in previous steps
    # Note: Phase 3 implementation modified classes to accept db_path or connection

    results = []

    try:
        # Benchmark 1: Graph Engine
        print("\n" + "=" * 60)
        print("1. GRAPH QUERY ENGINE")
        print("=" * 60 + "\n")

        engine = GraphQueryEngine(db_path=db_path)

        results.append(
            benchmark_component("Graph Build", lambda: engine.build_graph(), target_time=3.0)
        )

        results.append(
            benchmark_component(
                "Find Related Entities",
                lambda: engine.find_related_entities("entity_0", max_hops=3),
                target_time=2.0,
            )
        )

        results.append(
            benchmark_component(
                "Get Central Entities",
                lambda: engine.get_central_entities(top_n=20),
                target_time=2.0,
            )
        )

        # Benchmark 2: Context Analyzer
        print("\n" + "=" * 60)
        print("2. CONTEXT ANALYZER")
        print("=" * 60 + "\n")

        analyzer = ContextAnalyzer(db_path=db_path)

        results.append(
            benchmark_component(
                "Analyze Context",
                lambda: analyzer.analyze_current_context(recent_window_minutes=30),
                target_time=2.0,
            )
        )

        # Benchmark 3: Suggestion Engine
        print("\n" + "=" * 60)
        print("3. SUGGESTION ENGINE")
        print("=" * 60 + "\n")

        suggestion_engine = SuggestionEngine(db_path=db_path)

        results.append(
            benchmark_component(
                "Generate Suggestions",
                lambda: suggestion_engine.generate_suggestions(limit=10),
                target_time=2.0,
            )
        )

        # Benchmark 4: Pattern Detector
        print("\n" + "=" * 60)
        print("4. PATTERN DETECTOR")
        print("=" * 60 + "\n")

        detector = PatternDetector(db_path=db_path)

        results.append(
            benchmark_component(
                "Detect All Patterns",
                lambda: detector.detect_recurring_patterns(
                    days=30
                ),  # Method name fix from previous file
                target_time=5.0,
            )
        )

        # Benchmark 5: Clustering Service
        print("\n" + "=" * 60)
        print("5. CLUSTERING SERVICE")
        print("=" * 60 + "\n")

        clustering = ClusteringService(db_path=db_path)

        results.append(
            benchmark_component(
                "Get Cluster Reps",
                lambda: clustering.get_cluster_representatives(["perf_cog_1", "perf_cog_2"]),
                target_time=5.0,
            )
        )

        # Summary
        print("=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print()
        print(f"{'Component':<30} {'Avg (s)':<10} {'Target (s)':<12} {'Status':<8}")
        print("-" * 65)

        for result in results:
            status_symbol = "✅" if result["status"] == "pass" else "⚠️"
            if result["status"] == "fail":
                status_symbol = "❌"
            target_str = f"{result['target']}" if result["target"] else "N/A"
            print(
                f"{result['component']:<30} {result['avg']:<10.3f} {target_str:<12} {status_symbol:<8}"
            )

        print()

        return 0

    finally:
        test_db = Path(db_path)
        if test_db.exists():
            test_db.unlink()


if __name__ == "__main__":
    sys.exit(main())
