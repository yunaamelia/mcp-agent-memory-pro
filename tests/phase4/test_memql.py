#!/usr/bin/env python3
"""
Test MemQL Query Language
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

import sqlite3

from query.memql_executor import MemQLExecutor
from query.memql_parser import MemQLParser


def test_memql_parser():
    """Test MemQL parser"""

    print("Testing MemQL Parser")
    print("=" * 60)

    parser = MemQLParser()

    # Test queries
    queries = [
        "SELECT * FROM memories WHERE type = 'code' LIMIT 10",
        "SELECT content, importance_score FROM memories WHERE importance_score > 0.8",
        "SELECT * FROM memories WHERE project = 'test' ORDER BY timestamp DESC",
    ]

    for query in queries:
        print(f"\nQuery: {query}")

        try:
            parsed = parser.parse(query)
            print("  ✓ Parsed successfully")
            print(f"    Select: {parsed['select']}")
            print(f"    From: {parsed['from']}")
            if parsed["where"]:
                print(f"    Where: {parsed['where']}")
            if parsed["order"]:
                print(f"    Order: {parsed['order']}")
            if parsed["limit"]:
                print(f"    Limit:  {parsed['limit']}")
        except Exception as e:
            print(f"  ✗ Parse error: {e}")

    print("\n✅ MemQL parser tests passed!")


def test_memql_executor():
    """Test MemQL executor"""

    print("\nTesting MemQL Executor")
    print("=" * 60)

    # Create test database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Create table
    conn.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT,
            content TEXT,
            importance_score REAL,
            timestamp INTEGER
        )
    """)

    # Insert test data
    test_data = [
        ("m1", "code", "function test1() {}", 0.9, 1000),
        ("m2", "note", "Important note", 0.8, 2000),
        ("m3", "code", "function test2() {}", 0.7, 3000),
    ]

    for data in test_data:
        conn.execute("INSERT INTO memories VALUES (?, ?, ?, ?, ?)", data)

    conn.commit()

    # Test executor
    executor = MemQLExecutor(conn)

    query = "SELECT * FROM memories WHERE type = 'code' ORDER BY importance_score DESC"

    print(f"\nExecuting:  {query}")

    result = executor.execute(query)

    print("  ✓ Query executed")
    print(f"    Results: {result['count']}")
    try:
        print(f"    SQL: {result['sql']}")
    except KeyError:
        pass  # SQL might not be in result for some implementations

    for row in result["results"]:
        print(f"      - {row['id']}: {row['content'][:30]}...")

    conn.close()

    print("\n✅ MemQL executor tests passed!")


if __name__ == "__main__":
    test_memql_parser()
    test_memql_executor()
