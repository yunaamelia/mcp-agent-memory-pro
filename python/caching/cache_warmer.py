"""
Cache Warmer
Pre-loads frequently accessed data into cache
"""

import sqlite3

try:
    from caching.cache_manager import CacheManager
except ImportError:
    from .cache_manager import CacheManager


class CacheWarmer:
    """Warms up cache with frequently accessed data"""

    def __init__(self, db_connection: sqlite3.Connection, cache_manager: CacheManager):
        self.conn = db_connection
        self.conn.row_factory = sqlite3.Row
        self.cache = cache_manager

    def warm_frequent_searches(self):
        """Pre-cache results for frequent search queries"""

        try:
            # Get most accessed memories
            cursor = self.conn.execute("""
                SELECT id, type, content, importance_score, access_count
                FROM memories
                WHERE archived = 0
                ORDER BY access_count DESC
                LIMIT 100
            """)

            frequent_memories = [dict(row) for row in cursor.fetchall()]

            # Cache them
            for memory in frequent_memories:
                cache_key = f"memory_{memory['id']}"
                self.cache.set(cache_key, memory, ttl=3600, levels=["memory", "disk"])

            return len(frequent_memories)
        except sqlite3.OperationalError:
            return 0

    def warm_project_data(self):
        """Pre-cache project-specific data"""

        try:
            cursor = self.conn.execute("""
                SELECT DISTINCT project FROM memories
                WHERE project IS NOT NULL AND archived = 0
            """)

            projects = [row["project"] for row in cursor.fetchall()]

            for project in projects:
                # Cache project memories
                cursor = self.conn.execute(
                    """
                    SELECT * FROM memories
                    WHERE project = ? AND archived = 0
                    ORDER BY importance_score DESC
                    LIMIT 20
                """,
                    (project,),
                )

                memories = [dict(row) for row in cursor.fetchall()]
                cache_key = f"project_{project}_top"
                self.cache.set(cache_key, memories, ttl=1800, levels=["memory", "disk"])

            return len(projects)
        except sqlite3.OperationalError:
            return 0

    def warm_entity_graph(self):
        """Pre-cache entity graph data"""

        try:
            # Cache top entities
            cursor = self.conn.execute("""
                SELECT * FROM entities
                ORDER BY mention_count DESC
                LIMIT 50
            """)

            entities = [dict(row) for row in cursor.fetchall()]
            self.cache.set("top_entities", entities, ttl=3600, levels=["memory", "disk"])

            # Cache relationships
            cursor = self.conn.execute("""
                SELECT * FROM entity_relationships
                ORDER BY strength DESC
                LIMIT 100
            """)

            relationships = [dict(row) for row in cursor.fetchall()]
            self.cache.set("top_relationships", relationships, ttl=3600, levels=["memory", "disk"])

            return len(entities), len(relationships)
        except sqlite3.OperationalError:
            return 0, 0

    def warm_all(self):
        """Warm all caches"""

        print("Warming caches...")

        mem_count = self.warm_frequent_searches()
        print(f"  ✓ Frequent searches cached ({mem_count} memories)")

        proj_count = self.warm_project_data()
        print(f"  ✓ Project data cached ({proj_count} projects)")

        ent_count, rel_count = self.warm_entity_graph()
        print(f"  ✓ Entity graph cached ({ent_count} entities, {rel_count} relationships)")

        stats = self.cache.get_stats()
        print(f"\nCache stats: {stats}")

        return {
            "memories_cached": mem_count,
            "projects_cached": proj_count,
            "entities_cached": ent_count,
            "relationships_cached": rel_count,
            "stats": stats,
        }
