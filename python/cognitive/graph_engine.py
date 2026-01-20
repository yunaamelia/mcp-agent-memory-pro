"""
Graph Query Engine
Advanced graph traversal and relationship queries using NetworkX
"""

import sqlite3
import time
from pathlib import Path
from typing import Any

try:
    import networkx as nx
except ImportError:
    nx = None  # Will be checked at runtime


class GraphQueryEngine:
    """Engine for querying and traversing the knowledge graph"""

    def __init__(self, db_path: str | None = None):
        """
        Initialize the graph query engine.

        Args:
            db_path: Path to SQLite database. Defaults to standard data location.
        """
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "data" / "memory.db")

        self.db_path = db_path
        self._graph_cache: nx.Graph | None = None
        self._cache_timestamp: float = 0
        self._cache_duration: float = 300  # 5 minutes

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def build_graph(self, force_rebuild: bool = False) -> "nx.Graph":
        """
        Build NetworkX graph from database.

        Args:
            force_rebuild: Force rebuild even if cached

        Returns:
            NetworkX graph

        Raises:
            ImportError: If networkx is not installed
        """
        if nx is None:
            raise ImportError(
                "networkx is required for graph operations. Install with: uv pip install networkx"
            )

        current_time = time.time()

        # Use cache if recent
        if (
            not force_rebuild
            and self._graph_cache is not None
            and (current_time - self._cache_timestamp) < self._cache_duration
        ):
            return self._graph_cache

        G = nx.Graph()
        conn = self._get_db_connection()

        try:
            # Add entities as nodes
            cursor = conn.execute("""
                SELECT id, type, name, mention_count
                FROM entities
            """)

            for row in cursor.fetchall():
                G.add_node(
                    row["id"],
                    type=row["type"],
                    name=row["name"],
                    mention_count=row["mention_count"],
                )

            # Add relationships as edges
            cursor = conn.execute("""
                SELECT source_id, target_id, type, strength
                FROM entity_relationships
            """)

            for row in cursor.fetchall():
                G.add_edge(
                    row["source_id"],
                    row["target_id"],
                    rel_type=row["type"],
                    strength=row["strength"],
                )

            self._graph_cache = G
            self._cache_timestamp = current_time

            return G

        finally:
            conn.close()

    def find_related_entities(
        self, entity_id: str, max_hops: int = 2, min_strength: float = 0.3, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Find entities related to given entity using BFS traversal.

        Args:
            entity_id: Starting entity ID
            max_hops: Maximum relationship hops (default: 2)
            min_strength: Minimum relationship strength (default: 0.3)
            limit: Maximum results to return (default: 50)

        Returns:
            List of related entities with distances and strengths
        """
        G = self.build_graph()

        if entity_id not in G:
            return []

        # BFS with depth limit
        related = []
        visited = {entity_id}
        queue = [(entity_id, 0, 1.0)]  # (node, depth, cumulative_strength)

        while queue and len(related) < limit:
            current_id, depth, path_strength = queue.pop(0)

            if depth >= max_hops:
                continue

            for neighbor in G.neighbors(current_id):
                if neighbor in visited:
                    continue

                edge_data = G.get_edge_data(current_id, neighbor)
                strength = edge_data.get("strength", 0.5)

                if strength < min_strength:
                    continue

                visited.add(neighbor)
                node_data = G.nodes[neighbor]
                cumulative = path_strength * strength

                related.append(
                    {
                        "id": neighbor,
                        "type": node_data.get("type"),
                        "name": node_data.get("name"),
                        "distance": depth + 1,
                        "edge_strength": strength,
                        "path_strength": cumulative,
                        "mention_count": node_data.get("mention_count", 0),
                        "path_from": current_id,
                    }
                )

                queue.append((neighbor, depth + 1, cumulative))

        # Sort by path strength and distance
        related.sort(key=lambda x: (-x["path_strength"], x["distance"]))

        return related[:limit]

    def find_shortest_path(self, entity1_id: str, entity2_id: str) -> dict[str, Any] | None:
        """
        Find shortest path between two entities.

        Args:
            entity1_id: First entity
            entity2_id: Second entity

        Returns:
            Dict with path details, or None if no path exists
        """
        G = self.build_graph()

        if entity1_id not in G or entity2_id not in G:
            return None

        try:
            path = nx.shortest_path(G, entity1_id, entity2_id)

            # Build path details
            path_details = []
            total_strength = 1.0

            for i in range(len(path)):
                node_id = path[i]
                node_data = G.nodes[node_id]

                detail = {
                    "id": node_id,
                    "type": node_data.get("type"),
                    "name": node_data.get("name"),
                }

                if i > 0:
                    edge_data = G.get_edge_data(path[i - 1], node_id)
                    detail["edge_strength"] = edge_data.get("strength", 0.5)
                    total_strength *= detail["edge_strength"]

                path_details.append(detail)

            return {
                "path": path,
                "path_details": path_details,
                "length": len(path) - 1,
                "total_strength": total_strength,
            }

        except nx.NetworkXNoPath:
            return None

    def find_communities(self, min_size: int = 3) -> list[dict[str, Any]]:
        """
        Detect communities in the graph using greedy modularity.

        Args:
            min_size: Minimum community size (default: 3)

        Returns:
            List of communities with member details
        """
        G = self.build_graph()

        if len(G) < min_size:
            return []

        # Use greedy modularity communities
        from networkx.algorithms import community

        try:
            communities = community.greedy_modularity_communities(G)
        except Exception:
            return []

        # Filter by size and build result
        results = []
        for i, comm in enumerate(communities):
            if len(comm) < min_size:
                continue

            members = []
            for node_id in comm:
                node_data = G.nodes[node_id]
                members.append(
                    {
                        "id": node_id,
                        "type": node_data.get("type"),
                        "name": node_data.get("name"),
                        "mention_count": node_data.get("mention_count", 0),
                    }
                )

            # Sort by mention count
            members.sort(key=lambda x: -x["mention_count"])

            results.append(
                {
                    "community_id": i,
                    "size": len(comm),
                    "members": members,
                    "top_entities": [m["name"] for m in members[:5]],
                }
            )

        # Sort by size
        results.sort(key=lambda x: -x["size"])

        return results

    def get_central_entities(self, top_n: int = 10) -> list[dict[str, Any]]:
        """
        Get most central entities using PageRank.

        Args:
            top_n: Number of top entities to return (default: 10)

        Returns:
            List of entities with centrality scores
        """
        G = self.build_graph()

        if len(G) == 0:
            return []

        # Calculate PageRank
        try:
            pagerank = nx.pagerank(G, weight="strength")
        except Exception:
            return []

        # Sort and get top N
        sorted_entities = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:top_n]

        results = []
        for entity_id, score in sorted_entities:
            node_data = G.nodes[entity_id]
            results.append(
                {
                    "id": entity_id,
                    "type": node_data.get("type"),
                    "name": node_data.get("name"),
                    "centrality_score": round(score, 6),
                    "mention_count": node_data.get("mention_count", 0),
                    "degree": G.degree(entity_id),
                }
            )

        return results

    def find_bridging_entities(self, top_n: int = 10) -> list[dict[str, Any]]:
        """
        Find entities that bridge different communities.

        Args:
            top_n: Number of top bridging entities (default: 10)

        Returns:
            List of bridging entities with scores
        """
        G = self.build_graph()

        if len(G) < 3:
            return []

        # Calculate betweenness centrality
        try:
            betweenness = nx.betweenness_centrality(G, weight="strength")
        except Exception:
            return []

        sorted_entities = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:top_n]

        results = []
        for entity_id, score in sorted_entities:
            if score == 0:
                continue  # Skip non-bridging entities

            node_data = G.nodes[entity_id]
            results.append(
                {
                    "id": entity_id,
                    "type": node_data.get("type"),
                    "name": node_data.get("name"),
                    "bridging_score": round(score, 6),
                    "degree": G.degree(entity_id),
                }
            )

        return results

    def get_entity_neighborhood(self, entity_id: str, radius: int = 1) -> dict[str, Any]:
        """
        Get full neighborhood of an entity (ego graph).

        Args:
            entity_id: Entity to analyze
            radius: Neighborhood radius (default: 1)

        Returns:
            Dict with nodes and edges in neighborhood
        """
        G = self.build_graph()

        if entity_id not in G:
            return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

        # Get ego graph (subgraph centered on entity)
        ego_graph = nx.ego_graph(G, entity_id, radius=radius)

        nodes = []
        for node_id in ego_graph.nodes():
            node_data = ego_graph.nodes[node_id]
            nodes.append(
                {
                    "id": node_id,
                    "type": node_data.get("type"),
                    "name": node_data.get("name"),
                    "mention_count": node_data.get("mention_count", 0),
                    "is_center": node_id == entity_id,
                }
            )

        edges = []
        for source, target in ego_graph.edges():
            edge_data = ego_graph.get_edge_data(source, target)
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "strength": edge_data.get("strength", 0.5),
                    "type": edge_data.get("rel_type", "related_to"),
                }
            )

        return {
            "center_entity": entity_id,
            "radius": radius,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def get_graph_statistics(self) -> dict[str, Any]:
        """
        Get overall graph statistics.

        Returns:
            Dict with graph metrics
        """
        G = self.build_graph()

        if len(G) == 0:
            return {"node_count": 0, "edge_count": 0, "density": 0, "connected": False}

        stats = {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": round(nx.density(G), 6),
            "connected": nx.is_connected(G) if len(G) > 0 else False,
        }

        # Add component info
        if not stats["connected"]:
            components = list(nx.connected_components(G))
            stats["num_components"] = len(components)
            stats["largest_component_size"] = max(len(c) for c in components)

        # Average degree
        degrees = [d for n, d in G.degree()]
        if degrees:
            stats["avg_degree"] = round(sum(degrees) / len(degrees), 2)

        return stats


# Factory function for easy instantiation
def get_graph_engine(db_path: str | None = None) -> GraphQueryEngine:
    """Get a graph query engine instance."""
    return GraphQueryEngine(db_path=db_path)
