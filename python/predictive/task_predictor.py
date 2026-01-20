"""
Task Predictor
Predicts next tasks based on patterns
"""

import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any


class TaskPredictor:
    """Predicts next tasks based on historical patterns"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection

    def predict_next_tasks(
        self, current_context: dict[str, Any], limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Predict next tasks based on current context

        Args:
            current_context: Current work context
            limit: Number of predictions to return

        Returns:
            List of predicted tasks with confidence scores
        """

        predictions = []

        # 1. Temporal patterns (what usually comes next at this time)
        predictions.extend(self._predict_from_temporal_patterns(limit))

        # 2. Sequential patterns (what usually follows current work)
        if current_context.get("active_projects"):
            predictions.extend(
                self._predict_from_sequence(current_context["active_projects"][0], limit)
            )

        # 3. Unfinished tasks
        predictions.extend(self._get_unfinished_tasks(limit))

        # 4. Recurring patterns
        predictions.extend(self._predict_from_recurring_patterns(limit))

        # Sort by confidence and deduplicate
        predictions.sort(key=lambda x: x["confidence"], reverse=True)

        # Deduplicate
        seen = set()
        unique_predictions = []

        for pred in predictions:
            key = pred["task_type"] + "_" + pred.get("project", "")
            if key not in seen:
                seen.add(key)
                unique_predictions.append(pred)

        return unique_predictions[:limit]

    def _predict_from_temporal_patterns(self, limit: int) -> list[dict[str, Any]]:
        """Predict based on what usually happens at this time"""

        current_hour = datetime.now(UTC).hour
        current_day = datetime.now(UTC).weekday()

        # Get historical patterns for this time
        cursor = self.conn.execute(
            """
            SELECT type, project, COUNT(*) as frequency
            FROM memories
            WHERE CAST(strftime('%H', datetime(timestamp / 1000, 'unixepoch')) AS INTEGER) = ?
              AND CAST(strftime('%w', datetime(timestamp / 1000, 'unixepoch')) AS INTEGER) = ?
              AND archived = 0
              AND timestamp > ?
            GROUP BY type, project
            ORDER BY frequency DESC
            LIMIT ?
        """,
            (
                current_hour,
                current_day,
                int((datetime.now(UTC) - timedelta(days=90)).timestamp() * 1000),
                limit,
            ),
        )

        predictions = []

        for row in cursor.fetchall():
            predictions.append(
                {
                    "task_type": row["type"],
                    "project": row["project"],
                    "reason": f"You typically work on {row['type']} at this time",
                    "confidence": min(0.7, row["frequency"] / 10),
                    "source": "temporal_pattern",
                }
            )

        return predictions

    def _predict_from_sequence(self, current_project: str, limit: int) -> list[dict[str, Any]]:
        """Predict based on what usually follows current work"""

        # Get recent memory types in current project
        cursor = self.conn.execute(
            """
            SELECT type
            FROM memories
            WHERE project = ?
              AND archived = 0
            ORDER BY timestamp DESC
            LIMIT 5
        """,
            (current_project,),
        )

        recent_types = [row["type"] for row in cursor.fetchall()]

        if not recent_types:
            return []

        # Find what usually comes after these types
        cursor = self.conn.execute(
            """
            SELECT m2.type as next_type, COUNT(*) as frequency
            FROM memories m1
            JOIN memories m2 ON m2.timestamp > m1.timestamp
                AND m2.timestamp < m1.timestamp + 3600000  -- Within 1 hour
                AND m2.project = m1.project
            WHERE m1.type = ?
              AND m1.project = ?
              AND m1.archived = 0
            GROUP BY m2.type
            ORDER BY frequency DESC
            LIMIT ?
        """,
            (recent_types[0], current_project, limit),
        )

        predictions = []

        for row in cursor.fetchall():
            predictions.append(
                {
                    "task_type": row["next_type"],
                    "project": current_project,
                    "reason": f"Usually follows {recent_types[0]} work",
                    "confidence": min(0.8, row["frequency"] / 5),
                    "source": "sequential_pattern",
                }
            )

        return predictions

    def _get_unfinished_tasks(self, limit: int) -> list[dict[str, Any]]:
        """Get unfinished tasks (TODOs, etc.)"""

        cursor = self.conn.execute(
            """
            SELECT id, content, project, timestamp
            FROM memories
            WHERE type = 'note'
              AND (content LIKE '%TODO%' OR content LIKE '%FIXME%')
              AND archived = 0
            ORDER BY importance_score DESC, timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        predictions = []

        for row in cursor.fetchall():
            age_days = (datetime.now(UTC).timestamp() * 1000 - row["timestamp"]) / (
                24 * 60 * 60 * 1000
            )

            predictions.append(
                {
                    "task_type": "complete_todo",
                    "project": row["project"],
                    "task_id": row["id"],
                    "description": row["content"][:100],
                    "reason": f"Unfinished task ({int(age_days)} days old)",
                    "confidence": 0.9,
                    "source": "unfinished_task",
                }
            )

        return predictions

    def _predict_from_recurring_patterns(self, limit: int) -> list[dict[str, Any]]:
        """Predict based on recurring patterns"""

        # Find tasks that happen regularly
        cursor = self.conn.execute(
            """
            SELECT
                content,
                type,
                project,
                COUNT(*) as occurrences,
                AVG(timestamp) as avg_time
            FROM memories
            WHERE archived = 0
              AND timestamp > ?
            GROUP BY content, type, project
            HAVING occurrences >= 3
            ORDER BY occurrences DESC
            LIMIT ?
        """,
            (int((datetime.now(UTC) - timedelta(days=60)).timestamp() * 1000), limit),
        )

        predictions = []

        for row in cursor.fetchall():
            predictions.append(
                {
                    "task_type": row["type"],
                    "project": row["project"],
                    "description": row["content"][:100],
                    "reason": f"Recurring task (done {row['occurrences']} times)",
                    "confidence": min(0.85, row["occurrences"] / 10),
                    "source": "recurring_pattern",
                }
            )

        return predictions
