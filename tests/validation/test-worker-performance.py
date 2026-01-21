#!/usr/bin/env python3
"""
Test Worker Performance
Benchmarks worker execution times
"""

import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from services.ner_service import NERService
from services.scoring_service import ImportanceScoringService


def create_test_database(num_memories=100):
    """Create test database with sample data"""

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY, tier TEXT, type TEXT, source TEXT,
            content TEXT, timestamp INTEGER, project TEXT, tags TEXT,
            entities TEXT, importance_score REAL, access_count INTEGER,
            created_at INTEGER, archived INTEGER DEFAULT 0
        )
    """)

    now = int(datetime.now(UTC).timestamp() * 1000)

    for i in range(num_memories):
        conn.execute(
            """
            INSERT INTO memories
            (id, tier, type, source, content, timestamp, project, tags, importance_score, access_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                f"mem_{i}",
                "short",
                "code" if i % 2 == 0 else "note",
                "ide",
                f"function test{i}() {{ return {i}; }}",
                now - (i * 3600000),
                "test-project",
                '["test"]',
                0.5,
                i % 10,
                now,
            ),
        )

    conn.commit()
    return conn


def benchmark_scoring(conn, iterations=50):
    """Benchmark importance scoring"""

    print(f"Benchmarking Importance Scoring ({iterations} iterations)")
    print("-" * 40)

    scorer = ImportanceScoringService(conn)

    cursor = conn.execute("SELECT * FROM memories LIMIT 1")
    memory = dict(cursor.fetchone())
    memory["tags"] = ["test"]

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        scorer.calculate_importance(memory)
        end = time.perf_counter()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    print(f"  Avg: {avg_time * 1000:.2f}ms")
    print(f"  Min: {min_time * 1000:.2f}ms")
    print(f"  Max: {max_time * 1000:.2f}ms")

    # Target: < 10ms per scoring
    target = 0.010
    if avg_time < target:
        print(f"  ✅ Within target (<{target * 1000}ms)\n")
        return True
    else:
        print(f"  ⚠️ Exceeded target ({target * 1000}ms)\n")
        return False


def benchmark_ner(iterations=20):
    """Benchmark entity extraction"""

    print(f"Benchmarking Entity Extraction ({iterations} iterations)")
    print("-" * 40)

    ner = NERService()

    code = """
    import React from 'react';
    import axios from 'axios';

    async function fetchUserData(userId) {
        const response = await axios.get(`/api/users/${userId}`);
        return response.data;
    }

    class UserManager {
        constructor() {
            this.users = [];
        }

        async addUser(user) {
            this.users.push(user);
        }
    }
    """

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        ner.extract_entities(code, "code", {"language": "javascript"})
        end = time.perf_counter()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    print(f"  Avg: {avg_time * 1000:.2f}ms")
    print(f"  Min: {min_time * 1000:.2f}ms")
    print(f"  Max: {max_time * 1000:.2f}ms")

    # Target: < 50ms per extraction
    target = 0.050
    if avg_time < target:
        print(f"  ✅ Within target (<{target * 1000}ms)\n")
        return True
    else:
        print(f"  ⚠️ Exceeded target ({target * 1000}ms)\n")
        return False


def benchmark_batch_scoring(num_memories=100):
    """Benchmark batch scoring performance"""

    print(f"Benchmarking Batch Scoring ({num_memories} memories)")
    print("-" * 40)

    conn = create_test_database(num_memories)
    scorer = ImportanceScoringService(conn)

    cursor = conn.execute("SELECT * FROM memories")
    memories = [dict(row) for row in cursor.fetchall()]

    for mem in memories:
        mem["tags"] = ["test"]

    start = time.perf_counter()
    for memory in memories:
        scorer.calculate_importance(memory)
    end = time.perf_counter()

    total_time = end - start
    per_memory = total_time / num_memories

    print(f"  Total: {total_time * 1000:.2f}ms")
    print(f"  Per memory: {per_memory * 1000:.2f}ms")
    print(f"  Throughput: {num_memories / total_time:.0f} memories/sec")

    conn.close()

    # Target: process at least 100 memories per second
    if num_memories / total_time >= 100:
        print("  ✅ Throughput acceptable\n")
        return True
    else:
        print("  ⚠️ Throughput below target\n")
        return False


def main():
    """Run all performance benchmarks"""

    print("\n" + "=" * 50)
    print("WORKER PERFORMANCE BENCHMARKS")
    print("=" * 50 + "\n")

    warnings = 0

    conn = create_test_database(100)

    if not benchmark_scoring(conn, 50):
        warnings += 1

    if not benchmark_ner(20):
        warnings += 1

    conn.close()

    if not benchmark_batch_scoring(100):
        warnings += 1

    print("=" * 50)
    if warnings == 0:
        print("✅ ALL BENCHMARKS PASSED")
    else:
        print(f"⚠️ {warnings} BENCHMARK(S) EXCEEDED TARGETS")
    print("=" * 50)

    return 0 if warnings == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
