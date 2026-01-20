"""
Tests for Clustering Service
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))


@pytest.fixture
def test_db():
    """Create a test database"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            project TEXT,
            importance_score REAL DEFAULT 0.5,
            access_count INTEGER DEFAULT 0
        )
    """)

    # Insert test memories
    for i in range(10):
        conn.execute(
            """
            INSERT INTO memories (id, type, content, project, importance_score)
            VALUES (?, ?, ?, ?, ?)
        """,
            (f"m{i}", "code", f"Test content {i}", "test-project", 0.5 + i * 0.05),
        )

    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


class TestClusteringService:
    """Test cases for ClusteringService"""

    def test_initialization(self, test_db):
        """Test service initialization"""
        from cognitive.clustering_service import ClusteringService

        service = ClusteringService(db_path=test_db)
        assert service is not None

    def test_get_cluster_representatives(self, test_db):
        """Test getting cluster representatives"""
        from cognitive.clustering_service import ClusteringService

        service = ClusteringService(db_path=test_db)

        # Test with known memory IDs
        reps = service.get_cluster_representatives(["m0", "m1", "m2"], top_n=2)

        assert len(reps) <= 2
        assert all("id" in r for r in reps)

    def test_get_cluster_representatives_empty(self, test_db):
        """Test with empty cluster"""
        from cognitive.clustering_service import ClusteringService

        service = ClusteringService(db_path=test_db)

        reps = service.get_cluster_representatives([])

        assert reps == []


class TestClusteringServiceWithVectors:
    """Tests requiring vector database (may skip if not available)"""

    @pytest.mark.skip(reason="Requires vector database setup")
    def test_cluster_memories(self, test_db):
        """Test memory clustering"""
        from cognitive.clustering_service import ClusteringService

        service = ClusteringService(db_path=test_db)
        result = service.cluster_memories(min_cluster_size=2)

        assert "clusters" in result

    @pytest.mark.skip(reason="Requires vector database setup")
    def test_reduce_dimensions(self, test_db):
        """Test dimensionality reduction"""
        from cognitive.clustering_service import ClusteringService

        service = ClusteringService(db_path=test_db)
        result = service.reduce_dimensions(n_components=2)

        assert "points" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
