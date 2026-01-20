"""
Analytics Dashboard Service
Provides comprehensive analytics data
"""

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


class DashboardService:
    """Service for analytics dashboard"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection

    def get_overview(self) -> dict[str, Any]:
        """Get overview statistics"""

        stats = {}
        self.conn.row_factory = sqlite3.Row

        # Total memories
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM memories WHERE archived = 0")
        stats["total_memories"] = cursor.fetchone()["count"]

        # By tier
        cursor = self.conn.execute("""
            SELECT tier, COUNT(*) as count
            FROM memories
            WHERE archived = 0
            GROUP BY tier
        """)
        stats["by_tier"] = {row["tier"]: row["count"] for row in cursor.fetchall()}

        # By type
        cursor = self.conn.execute("""
            SELECT type, COUNT(*) as count
            FROM memories
            WHERE archived = 0
            GROUP BY type
        """)
        stats["by_type"] = {row["type"]: row["count"] for row in cursor.fetchall()}

        # Storage usage (estimate)
        cursor = self.conn.execute("""
            SELECT SUM(LENGTH(content)) as total_chars
            FROM memories
            WHERE archived = 0
        """)
        total_chars = cursor.fetchone()["total_chars"] or 0
        stats["storage_mb"] = round(total_chars / (1024 * 1024), 2)

        # Total entities
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM entities")
        stats["total_entities"] = cursor.fetchone()["count"]

        # Total relationships
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM entity_relationships")
        stats["total_relationships"] = cursor.fetchone()["count"]

        # Average importance
        cursor = self.conn.execute("""
            SELECT AVG(importance_score) as avg
            FROM memories
            WHERE archived = 0
        """)
        stats["avg_importance"] = round(cursor.fetchone()["avg"] or 0, 3)

        # Most active project
        cursor = self.conn.execute("""
            SELECT project, COUNT(*) as count
            FROM memories
            WHERE project IS NOT NULL AND archived = 0
            GROUP BY project
            ORDER BY count DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        stats["most_active_project"] = row["project"] if row else None

        return stats

    def get_activity_timeline(self, days: int = 30) -> list[dict[str, Any]]:
        """Get activity timeline"""

        cutoff = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)

        cursor = self.conn.execute(
            """
            SELECT DATE(timestamp / 1000, 'unixepoch') as date,
                   type,
                   COUNT(*) as count
            FROM memories
            WHERE timestamp > ?  AND archived = 0
            GROUP BY date, type
            ORDER BY date DESC
        """,
            (cutoff,),
        )

        timeline = defaultdict(lambda: {"date": None, "by_type": {}})

        for row in cursor.fetchall():
            date = row["date"]
            if timeline[date]["date"] is None:
                timeline[date]["date"] = date
            timeline[date]["by_type"][row["type"]] = row["count"]

        return list(timeline.values())

    def get_top_entities(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get top entities by mention count"""

        cursor = self.conn.execute(
            """
            SELECT type, name, mention_count
            FROM entities
            ORDER BY mention_count DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_project_breakdown(self) -> list[dict[str, Any]]:
        """Get breakdown by project"""

        cursor = self.conn.execute("""
            SELECT 
                project,
                COUNT(*) as memory_count,
                AVG(importance_score) as avg_importance,
                SUM(access_count) as total_accesses,
                MIN(timestamp) as first_memory,
                MAX(timestamp) as last_memory
            FROM memories
            WHERE project IS NOT NULL AND archived = 0
            GROUP BY project
            ORDER BY memory_count DESC
        """)

        projects = []
        for row in cursor.fetchall():
            projects.append(
                {
                    "project": row["project"],
                    "memory_count": row["memory_count"],
                    "avg_importance": round(row["avg_importance"], 3),
                    "total_accesses": row["total_accesses"],
                    # Handle possible NULL if no memories for project (though WHERE filters this) or python errors on timestamp conversion
                    "first_memory": datetime.fromtimestamp(row["first_memory"] / 1000, timezone.utc).isoformat()
                    if row["first_memory"]
                    else None,
                    "last_memory": datetime.fromtimestamp(row["last_memory"] / 1000, timezone.utc).isoformat()
                    if row["last_memory"]
                    else None,
                    "active_days": (row["last_memory"] - row["first_memory"])
                    / (24 * 60 * 60 * 1000)
                    if row["last_memory"] and row["first_memory"]
                    else 0,
                }
            )

        return projects

    def get_usage_stats(self) -> dict[str, Any]:
        """Get usage statistics"""

        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total_memories,
                SUM(access_count) as total_accesses,
                AVG(access_count) as avg_accesses,
                MAX(access_count) as max_accesses
            FROM memories
            WHERE archived = 0
        """)

        row = cursor.fetchone()

        # Get search stats - safely handle if table doesn't exist yet
        try:
            cursor = self.conn.execute("""
                SELECT value FROM statistics WHERE key = 'total_searches'
            """)
            search_row = cursor.fetchone()
            total_searches = int(search_row["value"]) if search_row else 0
        except sqlite3.OperationalError:
            total_searches = 0

        return {
            "total_memories": row["total_memories"],
            "total_accesses": row["total_accesses"] or 0,
            "avg_accesses_per_memory": round(row["avg_accesses"] or 0, 2),
            "max_accesses": row["max_accesses"] or 0,
            "total_searches": total_searches,
        }

    def get_health_metrics(self) -> dict[str, Any]:
        """Get system health metrics"""

        metrics = {}

        # Orphaned memories (no entities) - safely handle text fields
        cursor = self.conn.execute("""
            SELECT COUNT(*) as count
            FROM memories
            WHERE (entities IS NULL OR entities = '[]')
              AND archived = 0
              AND type = 'code'
        """)
        metrics["orphaned_code_memories"] = cursor.fetchone()["count"]

        # Unaccessed important memories
        cursor = self.conn.execute("""
            SELECT COUNT(*) as count
            FROM memories
            WHERE importance_score > 0.7
              AND access_count = 0
              AND archived = 0
        """)
        metrics["unaccessed_important"] = cursor.fetchone()["count"]

        # Old short-term memories
        week_ago = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp() * 1000)
        cursor = self.conn.execute(
            """
            SELECT COUNT(*) as count
            FROM memories
            WHERE tier = 'short'
              AND timestamp < ?
              AND archived = 0
        """,
            (week_ago,),
        )
        metrics["old_short_term"] = cursor.fetchone()["count"]

        # Calculate health score
        total_memories = self.conn.execute(
            "SELECT COUNT(*) as c FROM memories WHERE archived = 0"
        ).fetchone()["c"]

        health_score = 100

        if total_memories > 0:
            orphaned_ratio = metrics["orphaned_code_memories"] / total_memories
            unaccessed_ratio = metrics["unaccessed_important"] / total_memories
            old_short_ratio = metrics["old_short_term"] / total_memories

            health_score -= orphaned_ratio * 20
            health_score -= unaccessed_ratio * 15
            health_score -= old_short_ratio * 15

        metrics["health_score"] = max(0, int(health_score))

        return metrics
