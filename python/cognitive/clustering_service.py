"""
Clustering Service
Groups similar memories using advanced clustering algorithms
"""

import sqlite3
from pathlib import Path
from typing import Any

try:
    import numpy as np
except ImportError:
    np = None

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    AgglomerativeClustering = None
    cosine_similarity = None

try:
    import hdbscan
except ImportError:
    hdbscan = None

try:
    import umap
except ImportError:
    umap = None


class ClusteringService:
    """Groups similar memories using clustering algorithms"""

    def __init__(self, db_path: str | None = None, vector_path: str | None = None):
        """
        Initialize the clustering service.

        Args:
            db_path: Path to SQLite database
            vector_path: Path to vector database
        """
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "data" / "memory.db")
        if vector_path is None:
            vector_path = str(Path(__file__).parent.parent.parent / "data" / "vectors")

        self.db_path = db_path
        self.vector_path = vector_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def cluster_memories(
        self, project: str | None = None, min_cluster_size: int = 3, algorithm: str = "hdbscan"
    ) -> dict[str, Any]:
        """
        Cluster memories based on embedding similarity.

        Args:
            project: Optional project filter
            min_cluster_size: Minimum cluster size (default: 3)
            algorithm: Clustering algorithm ('hdbscan' or 'agglomerative')

        Returns:
            Clustering results with cluster assignments
        """
        if np is None:
            return {"error": "numpy not installed", "clusters": []}

        # Get memory vectors
        vectors, memory_ids = self._get_memory_vectors(project)

        if len(vectors) < min_cluster_size:
            return {
                "error": "Insufficient memories for clustering",
                "total_memories": len(vectors),
                "min_required": min_cluster_size,
                "clusters": [],
            }

        # Perform clustering
        if algorithm == "hdbscan" and hdbscan is not None:
            labels = self._cluster_hdbscan(vectors, min_cluster_size)
        elif AgglomerativeClustering is not None:
            labels = self._cluster_agglomerative(vectors, min_cluster_size)
        else:
            return {"error": "No clustering algorithm available", "clusters": []}

        # Build cluster results
        clusters = self._build_cluster_results(memory_ids, labels)

        return {
            "algorithm": algorithm,
            "total_memories": len(vectors),
            "num_clusters": len([c for c in clusters if c["cluster_id"] >= 0]),
            "noise_points": sum(1 for label in labels if label == -1),
            "clusters": clusters,
        }

    def reduce_dimensions(
        self, project: str | None = None, n_components: int = 2
    ) -> dict[str, Any]:
        """
        Reduce embedding dimensions for visualization using UMAP.

        Args:
            project: Optional project filter
            n_components: Target dimensions (default: 2)

        Returns:
            Reduced coordinates for each memory
        """
        if umap is None or np is None:
            return {"error": "umap-learn or numpy not installed", "points": []}

        vectors, memory_ids = self._get_memory_vectors(project)

        if len(vectors) < 5:
            return {
                "error": "Insufficient memories for dimensionality reduction",
                "total_memories": len(vectors),
                "points": [],
            }

        # Apply UMAP
        vectors_array = np.array(vectors)
        reducer = umap.UMAP(n_components=n_components, random_state=42)

        try:
            reduced = reducer.fit_transform(vectors_array)
        except Exception as e:
            return {"error": str(e), "points": []}

        # Build result with memory metadata
        conn = self._get_db_connection()
        try:
            points = []
            for i, memory_id in enumerate(memory_ids):
                cursor = conn.execute(
                    "SELECT type, project, content FROM memories WHERE id = ?", (memory_id,)
                )
                row = cursor.fetchone()

                point = {
                    "memory_id": memory_id,
                    "x": float(reduced[i][0]),
                    "y": float(reduced[i][1]),
                }

                if n_components >= 3:
                    point["z"] = float(reduced[i][2])

                if row:
                    point["type"] = row["type"]
                    point["project"] = row["project"]
                    point["content_preview"] = row["content"][:100] if row["content"] else ""

                points.append(point)

            return {"n_components": n_components, "total_points": len(points), "points": points}
        finally:
            conn.close()

    def get_cluster_representatives(
        self, cluster_members: list[str], top_n: int = 3
    ) -> list[dict[str, Any]]:
        """
        Get representative memories for a cluster.

        Args:
            cluster_members: List of memory IDs in cluster
            top_n: Number of representatives to return (default: 3)

        Returns:
            List of representative memories
        """
        if not cluster_members:
            return []

        conn = self._get_db_connection()

        try:
            # Get memories sorted by importance
            placeholders = ",".join("?" * len(cluster_members))
            cursor = conn.execute(
                f"""
                SELECT id, type, content, project, importance_score,
                       access_count
                FROM memories
                WHERE id IN ({placeholders})
                ORDER BY importance_score DESC, access_count DESC
                LIMIT ?
            """,
                (*cluster_members, top_n),
            )

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def calculate_cluster_coherence(self, cluster_members: list[str]) -> float:
        """
        Calculate coherence score for a cluster.

        Args:
            cluster_members: List of memory IDs in cluster

        Returns:
            Coherence score (0-1)
        """
        if len(cluster_members) < 2 or cosine_similarity is None or np is None:
            return 0.0

        # Get vectors for cluster members
        vectors = []

        try:
            import lancedb

            db = lancedb.connect(self.vector_path)
            table = db.open_table("memory_vectors")

            for memory_id in cluster_members:
                result = (
                    table.search([0] * 384).where(f'memory_id = "{memory_id}"').limit(1).to_list()
                )
                if result:
                    vectors.append(result[0]["vector"])
        except Exception:
            return 0.0

        if len(vectors) < 2:
            return 0.0

        # Calculate average pairwise similarity
        vectors_array = np.array(vectors)
        similarities = cosine_similarity(vectors_array)

        # Get upper triangle (excluding diagonal)
        n = len(vectors)
        total_sim = 0
        count = 0

        for i in range(n):
            for j in range(i + 1, n):
                total_sim += similarities[i][j]
                count += 1

        return float(total_sim / count) if count > 0 else 0.0

    def find_similar_memories(
        self, memory_id: str, top_n: int = 5, threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """
        Find memories similar to a given memory.

        Args:
            memory_id: Reference memory ID
            top_n: Number of similar memories (default: 5)
            threshold: Minimum similarity threshold (default: 0.7)

        Returns:
            List of similar memories with similarity scores
        """
        try:
            import lancedb

            db = lancedb.connect(self.vector_path)
            table = db.open_table("memory_vectors")

            # Get reference vector
            ref_result = (
                table.search([0] * 384).where(f'memory_id = "{memory_id}"').limit(1).to_list()
            )
            if not ref_result:
                return []

            ref_vector = ref_result[0]["vector"]

            # Search for similar
            results = table.search(ref_vector).limit(top_n + 1).to_list()

            # Get memory details
            conn = self._get_db_connection()
            try:
                similar = []
                for result in results:
                    if result["memory_id"] == memory_id:
                        continue

                    # Calculate similarity (1 - distance for cosine)
                    similarity = 1 - result.get("_distance", 0)

                    if similarity < threshold:
                        continue

                    cursor = conn.execute(
                        "SELECT id, type, content, project FROM memories WHERE id = ?",
                        (result["memory_id"],),
                    )
                    row = cursor.fetchone()

                    if row:
                        similar.append(
                            {
                                "memory_id": row["id"],
                                "type": row["type"],
                                "project": row["project"],
                                "content_preview": row["content"][:200] if row["content"] else "",
                                "similarity": round(similarity, 4),
                            }
                        )

                return similar[:top_n]
            finally:
                conn.close()

        except Exception as e:
            return [{"error": str(e)}]

    def _get_memory_vectors(
        self, project: str | None = None
    ) -> tuple[list[list[float]], list[str]]:
        """Get vectors and IDs for memories"""
        vectors = []
        memory_ids = []

        try:
            import lancedb

            db = lancedb.connect(self.vector_path)
            table = db.open_table("memory_vectors")

            # Get all vectors
            all_vectors = table.to_pandas()

            conn = self._get_db_connection()
            try:
                for _, row in all_vectors.iterrows():
                    memory_id = row["memory_id"]

                    # Filter by project if specified
                    if project:
                        cursor = conn.execute(
                            "SELECT project FROM memories WHERE id = ?", (memory_id,)
                        )
                        result = cursor.fetchone()
                        if not result or result["project"] != project:
                            continue

                    vectors.append(row["vector"])
                    memory_ids.append(memory_id)
            finally:
                conn.close()

        except Exception:
            pass

        return vectors, memory_ids

    def _cluster_hdbscan(self, vectors: list[list[float]], min_cluster_size: int) -> list[int]:
        """Cluster using HDBSCAN"""
        vectors_array = np.array(vectors)
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean")
        labels = clusterer.fit_predict(vectors_array)
        return labels.tolist()

    def _cluster_agglomerative(
        self, vectors: list[list[float]], min_cluster_size: int
    ) -> list[int]:
        """Cluster using Agglomerative Clustering"""
        vectors_array = np.array(vectors)
        n_clusters = max(2, len(vectors) // min_cluster_size)
        clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        labels = clusterer.fit_predict(vectors_array)
        return labels.tolist()

    def _build_cluster_results(
        self, memory_ids: list[str], labels: list[int]
    ) -> list[dict[str, Any]]:
        """Build cluster results with metadata"""
        from collections import defaultdict

        cluster_members: dict[int, list[str]] = defaultdict(list)

        for memory_id, label in zip(memory_ids, labels, strict=False):
            cluster_members[label].append(memory_id)

        conn = self._get_db_connection()
        try:
            clusters = []

            for cluster_id, members in sorted(cluster_members.items()):
                if cluster_id == -1:
                    continue  # Skip noise

                # Get metadata for cluster
                reps = self.get_cluster_representatives(members, top_n=1)

                cluster_info = {
                    "cluster_id": cluster_id,
                    "size": len(members),
                    "member_ids": members[:10],  # First 10
                    "representative": reps[0] if reps else None,
                }

                clusters.append(cluster_info)

            return clusters
        finally:
            conn.close()


# Factory function
def get_clustering_service(
    db_path: str | None = None, vector_path: str | None = None
) -> ClusteringService:
    """Get a clustering service instance."""
    return ClusteringService(db_path=db_path, vector_path=vector_path)
