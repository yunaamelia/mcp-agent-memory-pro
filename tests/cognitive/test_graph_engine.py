"""
Tests for Graph Query Engine
"""

import os
import sqlite3

# Add parent path for imports
import sys
import tempfile
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

    # Create tables
    conn.executescript("""
        CREATE TABLE entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            first_seen INTEGER,
            last_seen INTEGER,
            mention_count INTEGER DEFAULT 1
        );

        CREATE TABLE entity_relationships (
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            type TEXT NOT NULL,
            strength REAL DEFAULT 0.5,
            created_at INTEGER,
            updated_at INTEGER,
            PRIMARY KEY (source_id, target_id, type)
        );
    """)

    # Insert test entities
    entities = [
        ("e1", "function", "handleAuth", 5),
        ("e2", "class", "UserService", 8),
        ("e3", "function", "validateToken", 3),
        ("e4", "module", "auth", 10),
        ("e5", "function", "createUser", 4),
    ]

    for eid, etype, name, mentions in entities:
        conn.execute(
            "INSERT INTO entities (id, type, name, mention_count, first_seen, last_seen) VALUES (?, ?, ?, ?, 0, 0)",
            (eid, etype, name, mentions),
        )

    # Insert relationships
    relationships = [
        ("e1", "e2", "related_to", 0.8),
        ("e1", "e3", "related_to", 0.9),
        ("e2", "e4", "related_to", 0.7),
        ("e2", "e5", "related_to", 0.6),
        ("e3", "e4", "related_to", 0.85),
    ]

    for source, target, rtype, strength in relationships:
        conn.execute(
            "INSERT INTO entity_relationships (source_id, target_id, type, strength, created_at, updated_at) VALUES (?, ?, ?, ?, 0, 0)",
            (source, target, rtype, strength),
        )

    conn.commit()
    conn.close()

    yield path

    # Cleanup
    os.unlink(path)


class TestGraphQueryEngine:
    """Test cases for GraphQueryEngine"""

    def test_build_graph(self, test_db):
        """Test graph building from database"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)
        graph = engine.build_graph()

        assert graph.number_of_nodes() == 5
        assert graph.number_of_edges() == 5

    def test_build_graph_caching(self, test_db):
        """Test that graph is cached"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        graph1 = engine.build_graph()
        graph2 = engine.build_graph()

        # Should be the same cached object
        assert graph1 is graph2

    def test_build_graph_force_rebuild(self, test_db):
        """Test force rebuild of graph"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        graph1 = engine.build_graph()
        graph2 = engine.build_graph(force_rebuild=True)

        # Should be different objects
        assert graph1 is not graph2

    def test_find_related_entities(self, test_db):
        """Test finding related entities"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        related = engine.find_related_entities("e1", max_hops=1)

        assert len(related) > 0
        assert all(r["distance"] == 1 for r in related)

    def test_find_related_entities_multi_hop(self, test_db):
        """Test multi-hop relationship traversal"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        related = engine.find_related_entities("e1", max_hops=2)

        # Should find entities at distance 1 and 2
        distances = {r["distance"] for r in related}
        assert 1 in distances
        assert 2 in distances

    def test_find_related_entities_strength_filter(self, test_db):
        """Test minimum strength filtering"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        related = engine.find_related_entities("e1", max_hops=2, min_strength=0.8)

        # All relationships should meet minimum strength
        assert all(r["edge_strength"] >= 0.8 for r in related)

    def test_find_related_entities_nonexistent(self, test_db):
        """Test with nonexistent entity"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        related = engine.find_related_entities("nonexistent")

        assert related == []

    def test_find_shortest_path(self, test_db):
        """Test finding shortest path"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        result = engine.find_shortest_path("e1", "e4")

        assert result is not None
        assert "path" in result
        assert result["path"][0] == "e1"
        assert result["path"][-1] == "e4"

    def test_find_shortest_path_no_path(self, test_db):
        """Test when no path exists"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        # Add isolated node
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO entities (id, type, name, mention_count) VALUES (?, ?, ?, ?)",
            ("isolated", "test", "Isolated", 1),
        )
        conn.commit()
        conn.close()

        # Force rebuild
        engine._graph_cache = None

        result = engine.find_shortest_path("e1", "isolated")

        assert result is None

    def test_get_central_entities(self, test_db):
        """Test getting central entities"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        central = engine.get_central_entities(top_n=3)

        assert len(central) <= 3
        assert all("centrality_score" in e for e in central)

    def test_find_bridging_entities(self, test_db):
        """Test finding bridging entities"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        bridging = engine.find_bridging_entities(top_n=3)

        assert isinstance(bridging, list)
        for entity in bridging:
            assert "bridging_score" in entity

    def test_get_entity_neighborhood(self, test_db):
        """Test getting entity neighborhood"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        neighborhood = engine.get_entity_neighborhood("e2", radius=1)

        assert neighborhood["center_entity"] == "e2"
        assert len(neighborhood["nodes"]) > 0
        assert any(n["is_center"] for n in neighborhood["nodes"])

    def test_get_graph_statistics(self, test_db):
        """Test getting graph statistics"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        stats = engine.get_graph_statistics()

        assert stats["node_count"] == 5
        assert stats["edge_count"] == 5
        assert "density" in stats
        assert "connected" in stats

    def test_find_communities(self, test_db):
        """Test community detection"""
        from cognitive.graph_engine import GraphQueryEngine

        engine = GraphQueryEngine(db_path=test_db)

        communities = engine.find_communities(min_size=2)

        assert isinstance(communities, list)
        for community in communities:
            assert "size" in community
            assert community["size"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
