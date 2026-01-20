"""
Pattern Analyzer Worker
Periodically analyzes memory patterns and stores insights
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from workers.base_worker import BaseWorker


class PatternAnalyzerWorker(BaseWorker):
    """Worker that analyzes patterns and stores insights"""

    def __init__(self):
        super().__init__("PatternAnalyzer")
        self.pattern_detector = None

    def _get_services(self):
        """Lazy load cognitive services"""
        if self.pattern_detector is None:
            try:
                from cognitive.pattern_detector import get_pattern_detector

                db_path = str(Path(__file__).parent.parent.parent / "data" / "memory.db")
                self.pattern_detector = get_pattern_detector(db_path)
            except ImportError as e:
                self.logger.error(f"Failed to import pattern detector: {e}")
                raise

    def process(self) -> dict[str, Any]:
        """Run pattern analysis"""

        self._get_services()

        results = {
            "patterns_detected": 0,
            "anomalies_detected": 0,
            "trends_analyzed": 0,
            "insights_stored": 0,
            "errors": [],
        }

        conn = self.get_db_connection()

        try:
            # Step 1: Detect recurring patterns
            try:
                patterns = self.pattern_detector.detect_recurring_patterns(
                    days=14, min_occurrences=3
                )
                results["patterns_detected"] = len(patterns)

                # Store significant patterns as insights
                for pattern in patterns[:5]:  # Top 5 patterns
                    self._store_pattern_insight(conn, pattern)
                    results["insights_stored"] += 1

                self.logger.info(f"Detected {len(patterns)} recurring patterns")

            except Exception as e:
                results["errors"].append(f"Pattern detection error: {e!s}")
                self.logger.error(f"Pattern detection failed: {e}")

            # Step 2: Identify anomalies
            try:
                anomalies = self.pattern_detector.identify_anomalies(days=7)
                results["anomalies_detected"] = len(anomalies)

                # Store significant anomalies
                for anomaly in anomalies:
                    if anomaly.get("severity") in ["high", "medium"]:
                        self._store_anomaly_alert(conn, anomaly)
                        results["insights_stored"] += 1

                self.logger.info(f"Detected {len(anomalies)} anomalies")

            except Exception as e:
                results["errors"].append(f"Anomaly detection error: {e!s}")
                self.logger.error(f"Anomaly detection failed: {e}")

            # Step 3: Track trends for active projects
            try:
                # Get active projects
                cursor = conn.execute("""
                    SELECT DISTINCT project
                    FROM memories
                    WHERE project IS NOT NULL AND archived = 0
                    ORDER BY MAX(timestamp) DESC
                    LIMIT 5
                """)
                projects = [row["project"] for row in cursor.fetchall()]

                for project in projects:
                    trend = self.pattern_detector.track_trends(project=project, days=30)
                    results["trends_analyzed"] += 1

                    # Store significant trend changes
                    if trend.get("trend_direction") in ["increasing", "decreasing"]:
                        if abs(trend.get("trend_ratio", 0)) > 0.5:
                            self._store_trend_insight(conn, project, trend)
                            results["insights_stored"] += 1

                self.logger.info(f"Analyzed trends for {len(projects)} projects")

            except Exception as e:
                results["errors"].append(f"Trend analysis error: {e!s}")
                self.logger.error(f"Trend analysis failed: {e}")

            conn.commit()

        finally:
            conn.close()

        return {
            "processed": results["insights_stored"],
            "skipped": 0,
            "errors": len(results["errors"]),
            "details": results,
        }

    def _store_pattern_insight(self, conn, pattern: dict[str, Any]):
        """Store a pattern as an insight memory"""
        import hashlib
        import uuid

        content = f"Pattern Detected: {pattern.get('description', 'Unknown pattern')}\n"
        content += f"Type: {pattern.get('type')}\n"
        content += f"Frequency: {pattern.get('frequency')}\n"

        if pattern.get("entities"):
            content += f"Entities: {', '.join(pattern['entities'])}\n"

        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if similar insight already exists
        existing = conn.execute(
            "SELECT id FROM memories WHERE content_hash = ?", (content_hash,)
        ).fetchone()

        if existing:
            return  # Skip duplicate

        now = int(datetime.now().timestamp() * 1000)

        conn.execute(
            """
            INSERT INTO memories (
                id, tier, type, source, content, content_hash,
                timestamp, importance_score, created_at, archived
            ) VALUES (?, 'working', 'insight', 'pattern_analyzer', ?, ?, ?, 0.7, ?, 0)
        """,
            (str(uuid.uuid4()), content, content_hash, now, now),
        )

    def _store_anomaly_alert(self, conn, anomaly: dict[str, Any]):
        """Store an anomaly as an alert memory"""
        import hashlib
        import uuid

        severity = anomaly.get("severity", "medium")
        importance = 0.9 if severity == "high" else 0.7

        content = f"Anomaly Alert ({severity}): {anomaly.get('description', 'Unknown anomaly')}\n"
        content += f"Type: {anomaly.get('type')}\n"

        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if similar alert exists recently
        existing = conn.execute(
            "SELECT id FROM memories WHERE content_hash = ?", (content_hash,)
        ).fetchone()

        if existing:
            return

        now = int(datetime.now().timestamp() * 1000)

        conn.execute(
            """
            INSERT INTO memories (
                id, tier, type, source, content, content_hash,
                timestamp, importance_score, created_at, archived
            ) VALUES (?, 'short', 'insight', 'pattern_analyzer', ?, ?, ?, ?, ?, 0)
        """,
            (str(uuid.uuid4()), content, content_hash, now, importance, now),
        )

    def _store_trend_insight(self, conn, project: str, trend: dict[str, Any]):
        """Store a trend insight"""
        import hashlib
        import uuid

        direction = trend.get("trend_direction", "stable")
        ratio = trend.get("trend_ratio", 0)

        content = f"Trend Analysis for {project}:\n"
        content += f"Direction: {direction} ({ratio:+.1%})\n"
        content += f"Activity: {trend.get('total_count', 0)} memories over {trend.get('period_days', 30)} days\n"

        content_hash = hashlib.sha256((content + str(datetime.now().date())).encode()).hexdigest()

        # One trend insight per project per day
        existing = conn.execute(
            "SELECT id FROM memories WHERE content_hash = ?", (content_hash,)
        ).fetchone()

        if existing:
            return

        now = int(datetime.now().timestamp() * 1000)

        conn.execute(
            """
            INSERT INTO memories (
                id, tier, type, source, content, content_hash,
                timestamp, project, importance_score, created_at, archived
            ) VALUES (?, 'working', 'insight', 'pattern_analyzer', ?, ?, ?, ?, 0.6, ?, 0)
        """,
            (str(uuid.uuid4()), content, content_hash, now, project, now),
        )


if __name__ == "__main__":
    worker = PatternAnalyzerWorker()
    result = worker.run()
    print(f"Result: {result}")
