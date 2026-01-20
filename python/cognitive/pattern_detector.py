"""
Pattern Detector
Detects recurring patterns, anomalies, and trends in memory data
"""

import json
import sqlite3
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class PatternDetector:
    """Detects patterns, anomalies, and trends in memory data"""

    def __init__(self, db_path: str | None = None):
        """
        Initialize the pattern detector.

        Args:
            db_path: Path to SQLite database. Defaults to standard data location.
        """
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "data" / "memory.db")

        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def detect_recurring_patterns(
        self, days: int = 30, min_occurrences: int = 3
    ) -> list[dict[str, Any]]:
        """
        Detect recurring behavior patterns.

        Args:
            days: Number of days to analyze (default: 30)
            min_occurrences: Minimum occurrences to be considered a pattern (default: 3)

        Returns:
            List of detected patterns with frequencies
        """
        conn = self._get_db_connection()

        try:
            cutoff_time = int((datetime.now(UTC) - timedelta(days=days)).timestamp() * 1000)

            patterns = []

            # Detect entity co-occurrence patterns
            entity_patterns = self._detect_entity_patterns(conn, cutoff_time, min_occurrences)
            patterns.extend(entity_patterns)

            # Detect time-based patterns
            time_patterns = self._detect_time_patterns(conn, cutoff_time)
            patterns.extend(time_patterns)

            # Detect project workflow patterns
            workflow_patterns = self._detect_workflow_patterns(conn, cutoff_time, min_occurrences)
            patterns.extend(workflow_patterns)

            # Sort by frequency
            patterns.sort(key=lambda x: -x.get("frequency", 0))

            return patterns

        finally:
            conn.close()

    def identify_anomalies(self, days: int = 7) -> list[dict[str, Any]]:
        """
        Identify anomalies in recent activity.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            List of detected anomalies
        """
        conn = self._get_db_connection()

        try:
            anomalies = []

            # Compare recent activity to baseline
            recent_cutoff = int((datetime.now(UTC) - timedelta(days=days)).timestamp() * 1000)
            baseline_start = int((datetime.now(UTC) - timedelta(days=days * 4)).timestamp() * 1000)

            # Analyze activity volume
            volume_anomalies = self._detect_volume_anomalies(
                conn, recent_cutoff, baseline_start, days
            )
            anomalies.extend(volume_anomalies)

            # Analyze error rate
            error_anomalies = self._detect_error_anomalies(conn, recent_cutoff, baseline_start)
            anomalies.extend(error_anomalies)

            # Analyze project switching
            switch_anomalies = self._detect_context_switch_anomalies(conn, recent_cutoff)
            anomalies.extend(switch_anomalies)

            return anomalies

        finally:
            conn.close()

    def track_trends(
        self, entity: str | None = None, project: str | None = None, days: int = 30
    ) -> dict[str, Any]:
        """
        Track trends over time.

        Args:
            entity: Optional entity to track
            project: Optional project to track
            days: Number of days to analyze (default: 30)

        Returns:
            Trend analysis with direction and magnitude
        """
        conn = self._get_db_connection()

        try:
            int((datetime.now(UTC) - timedelta(days=days)).timestamp() * 1000)

            # Divide into periods
            period_days = days // 4
            periods = []

            for i in range(4):
                period_end = int(
                    (datetime.now(UTC) - timedelta(days=i * period_days)).timestamp() * 1000
                )
                period_start = int(
                    (datetime.now(UTC) - timedelta(days=(i + 1) * period_days)).timestamp() * 1000
                )

                # Count memories in period
                query = "SELECT COUNT(*) as count FROM memories WHERE timestamp > ? AND timestamp <= ? AND archived = 0"
                params: list[Any] = [period_start, period_end]

                if entity:
                    query += " AND entities LIKE ?"
                    params.append(f"%{entity}%")

                if project:
                    query += " AND project = ?"
                    params.append(project)

                cursor = conn.execute(query, params)
                count = cursor.fetchone()["count"]
                periods.append(count)

            # Reverse to chronological order
            periods.reverse()

            # Calculate trend
            if len(periods) >= 2 and periods[0] > 0:
                trend_ratio = (periods[-1] - periods[0]) / periods[0]

                if trend_ratio > 0.3:
                    trend_direction = "increasing"
                elif trend_ratio < -0.3:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_ratio = 0
                trend_direction = "insufficient_data"

            return {
                "entity": entity,
                "project": project,
                "period_days": days,
                "period_counts": periods,
                "trend_direction": trend_direction,
                "trend_ratio": round(trend_ratio, 3),
                "total_count": sum(periods),
                "average_per_period": round(sum(periods) / len(periods), 1) if periods else 0,
            }

        finally:
            conn.close()

    def get_pattern_statistics(self) -> dict[str, Any]:
        """
        Get summary statistics on detected patterns.

        Returns:
            Statistics summary
        """
        conn = self._get_db_connection()

        try:
            stats = {}

            # Total memories
            cursor = conn.execute("SELECT COUNT(*) as count FROM memories WHERE archived = 0")
            stats["total_memories"] = cursor.fetchone()["count"]

            # Memories by type
            cursor = conn.execute("""
                SELECT type, COUNT(*) as count
                FROM memories
                WHERE archived = 0
                GROUP BY type
                ORDER BY count DESC
            """)
            stats["memories_by_type"] = {row["type"]: row["count"] for row in cursor.fetchall()}

            # Memories by project
            cursor = conn.execute("""
                SELECT project, COUNT(*) as count
                FROM memories
                WHERE archived = 0 AND project IS NOT NULL
                GROUP BY project
                ORDER BY count DESC
                LIMIT 10
            """)
            stats["top_projects"] = {row["project"]: row["count"] for row in cursor.fetchall()}

            # Entity count
            cursor = conn.execute("SELECT COUNT(*) as count FROM entities")
            stats["total_entities"] = cursor.fetchone()["count"]

            # Relationship count
            cursor = conn.execute("SELECT COUNT(*) as count FROM entity_relationships")
            stats["total_relationships"] = cursor.fetchone()["count"]

            # Average importance
            cursor = conn.execute("""
                SELECT AVG(importance_score) as avg_importance
                FROM memories
                WHERE archived = 0
            """)
            result = cursor.fetchone()
            stats["avg_importance"] = (
                round(result["avg_importance"], 3) if result["avg_importance"] else 0
            )

            # Recent activity (last 24h)
            day_ago = int((datetime.now(UTC) - timedelta(days=1)).timestamp() * 1000)
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM memories
                WHERE timestamp > ? AND archived = 0
            """,
                (day_ago,),
            )
            stats["memories_last_24h"] = cursor.fetchone()["count"]

            return stats

        finally:
            conn.close()

    def _detect_entity_patterns(
        self, conn: sqlite3.Connection, cutoff_time: int, min_occurrences: int
    ) -> list[dict[str, Any]]:
        """Detect entities that frequently co-occur"""
        cursor = conn.execute(
            """
            SELECT entities
            FROM memories
            WHERE timestamp > ? AND archived = 0 AND entities IS NOT NULL
        """,
            (cutoff_time,),
        )

        # Count entity pairs
        pair_counts: Counter[tuple[str, str]] = Counter()

        for row in cursor.fetchall():
            try:
                entities = json.loads(row["entities"])
                if len(entities) >= 2:
                    # Generate all pairs
                    for i, e1 in enumerate(entities):
                        for e2 in entities[i + 1 :]:
                            pair = tuple(sorted([e1, e2]))
                            pair_counts[pair] += 1
            except (json.JSONDecodeError, TypeError):
                pass

        # Filter by min occurrences
        patterns = []
        for pair, count in pair_counts.most_common(10):
            if count >= min_occurrences:
                patterns.append(
                    {
                        "type": "entity_co_occurrence",
                        "entities": list(pair),
                        "frequency": count,
                        "description": f"Entities '{pair[0]}' and '{pair[1]}' frequently appear together",
                    }
                )

        return patterns

    def _detect_time_patterns(
        self, conn: sqlite3.Connection, cutoff_time: int
    ) -> list[dict[str, Any]]:
        """Detect time-based activity patterns"""
        cursor = conn.execute(
            """
            SELECT timestamp
            FROM memories
            WHERE timestamp > ? AND archived = 0
        """,
            (cutoff_time,),
        )

        hour_counts: Counter[int] = Counter()
        day_counts: Counter[int] = Counter()

        for row in cursor.fetchall():
            dt = datetime.fromtimestamp(row["timestamp"] / 1000, UTC)
            hour_counts[dt.hour] += 1
            day_counts[dt.weekday()] += 1

        patterns = []

        # Find peak hours
        if hour_counts:
            peak_hour, peak_count = hour_counts.most_common(1)[0]
            patterns.append(
                {
                    "type": "peak_activity_hour",
                    "hour": peak_hour,
                    "frequency": peak_count,
                    "description": f"Most active hour: {peak_hour}:00-{peak_hour + 1}:00",
                }
            )

        # Find peak days
        if day_counts:
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            peak_day, day_count = day_counts.most_common(1)[0]
            patterns.append(
                {
                    "type": "peak_activity_day",
                    "day": day_names[peak_day],
                    "frequency": day_count,
                    "description": f"Most active day: {day_names[peak_day]}",
                }
            )

        return patterns

    def _detect_workflow_patterns(
        self, conn: sqlite3.Connection, cutoff_time: int, min_occurrences: int
    ) -> list[dict[str, Any]]:
        """Detect common workflow patterns"""
        cursor = conn.execute(
            """
            SELECT type, project
            FROM memories
            WHERE timestamp > ? AND archived = 0
            ORDER BY timestamp
        """,
            (cutoff_time,),
        )

        # Track type sequences
        sequence_counts: Counter[tuple[str, str]] = Counter()
        prev_type = None

        for row in cursor.fetchall():
            current_type = row["type"]
            if prev_type and current_type:
                sequence_counts[(prev_type, current_type)] += 1
            prev_type = current_type

        patterns = []
        for (type1, type2), count in sequence_counts.most_common(5):
            if count >= min_occurrences:
                patterns.append(
                    {
                        "type": "workflow_sequence",
                        "sequence": [type1, type2],
                        "frequency": count,
                        "description": f"'{type1}' often followed by '{type2}'",
                    }
                )

        return patterns

    def _detect_volume_anomalies(
        self, conn: sqlite3.Connection, recent_cutoff: int, baseline_start: int, days: int
    ) -> list[dict[str, Any]]:
        """Detect anomalies in activity volume"""
        # Recent volume
        cursor = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM memories
            WHERE timestamp > ? AND archived = 0
        """,
            (recent_cutoff,),
        )
        recent_count = cursor.fetchone()["count"]

        # Baseline volume (normalized to same period)
        cursor = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM memories
            WHERE timestamp > ? AND timestamp <= ? AND archived = 0
        """,
            (baseline_start, recent_cutoff),
        )
        baseline_count = cursor.fetchone()["count"] / 3  # Normalize

        anomalies = []

        if baseline_count > 0:
            ratio = recent_count / baseline_count

            if ratio > 1.5:
                anomalies.append(
                    {
                        "type": "high_activity_volume",
                        "severity": "medium",
                        "recent_count": recent_count,
                        "baseline_avg": round(baseline_count, 1),
                        "ratio": round(ratio, 2),
                        "description": f"Activity is {ratio:.1f}x higher than baseline",
                    }
                )
            elif ratio < 0.5:
                anomalies.append(
                    {
                        "type": "low_activity_volume",
                        "severity": "low",
                        "recent_count": recent_count,
                        "baseline_avg": round(baseline_count, 1),
                        "ratio": round(ratio, 2),
                        "description": f"Activity is {ratio:.1f}x lower than baseline",
                    }
                )

        return anomalies

    def _detect_error_anomalies(
        self, conn: sqlite3.Connection, recent_cutoff: int, baseline_start: int
    ) -> list[dict[str, Any]]:
        """Detect anomalies in error rate"""
        # Recent errors
        cursor = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM memories
            WHERE timestamp > ? AND archived = 0
              AND (content LIKE '%error%' OR content LIKE '%Error%' OR content LIKE '%exception%')
        """,
            (recent_cutoff,),
        )
        recent_errors = cursor.fetchone()["count"]

        # Baseline errors
        cursor = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM memories
            WHERE timestamp > ? AND timestamp <= ? AND archived = 0
              AND (content LIKE '%error%' OR content LIKE '%Error%' OR content LIKE '%exception%')
        """,
            (baseline_start, recent_cutoff),
        )
        baseline_errors = cursor.fetchone()["count"] / 3

        anomalies = []

        if baseline_errors > 0 and recent_errors > baseline_errors * 2:
            anomalies.append(
                {
                    "type": "high_error_rate",
                    "severity": "high",
                    "recent_errors": recent_errors,
                    "baseline_avg": round(baseline_errors, 1),
                    "description": f"Error rate is significantly higher than baseline ({recent_errors} vs avg {baseline_errors:.1f})",
                }
            )

        return anomalies

    def _detect_context_switch_anomalies(
        self, conn: sqlite3.Connection, recent_cutoff: int
    ) -> list[dict[str, Any]]:
        """Detect excessive context switching"""
        cursor = conn.execute(
            """
            SELECT project, timestamp
            FROM memories
            WHERE timestamp > ? AND archived = 0 AND project IS NOT NULL
            ORDER BY timestamp
        """,
            (recent_cutoff,),
        )

        # Count project switches
        switches = 0
        prev_project = None

        for row in cursor.fetchall():
            if prev_project and row["project"] != prev_project:
                switches += 1
            prev_project = row["project"]

        anomalies = []

        # Threshold: more than 10 switches per day
        if switches > 10:
            anomalies.append(
                {
                    "type": "high_context_switching",
                    "severity": "medium",
                    "switch_count": switches,
                    "description": f"High project context switching detected ({switches} switches)",
                }
            )

        return anomalies


# Factory function
def get_pattern_detector(db_path: str | None = None) -> PatternDetector:
    """Get a pattern detector instance."""
    return PatternDetector(db_path=db_path)
