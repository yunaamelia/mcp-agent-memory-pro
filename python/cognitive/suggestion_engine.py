"""
Suggestion Engine
Generates proactive suggestions based on memory patterns and context
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class SuggestionEngine:
    """Generates smart suggestions based on memory patterns and current context"""

    def __init__(self, db_path: str | None = None):
        """
        Initialize the suggestion engine.

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

    def generate_suggestions(
        self, context: dict[str, Any] | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Generate actionable suggestions based on context.

        Args:
            context: Current context analysis (from ContextAnalyzer)
            limit: Maximum suggestions to return (default: 5)

        Returns:
            List of suggestions with types and priorities
        """
        suggestions = []

        # Get various suggestion types
        suggestions.extend(self._get_forgotten_knowledge_suggestions(context, limit=2))
        suggestions.extend(self._get_pattern_based_suggestions(context, limit=2))
        suggestions.extend(self._get_issue_suggestions(context, limit=2))
        suggestions.extend(self._get_best_practice_suggestions(context, limit=2))

        # Sort by priority and limit
        suggestions.sort(key=lambda x: -x.get("priority", 0))

        return suggestions[:limit]

    def detect_potential_issues(
        self, project: str | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Detect potential issues based on memory patterns.

        Args:
            project: Optional project to focus on
            limit: Maximum issues to return (default: 5)

        Returns:
            List of potential issues with descriptions
        """
        conn = self._get_db_connection()
        issues = []

        try:
            # Find unresolved TODOs
            todo_issues = self._find_unresolved_todos(conn, project)
            issues.extend(todo_issues)

            # Find repeated errors
            error_issues = self._find_repeated_errors(conn, project)
            issues.extend(error_issues)

            # Find stale important memories
            stale_issues = self._find_stale_important_memories(conn, project)
            issues.extend(stale_issues)

            # Sort by severity
            severity_order = {"high": 3, "medium": 2, "low": 1}
            issues.sort(key=lambda x: -severity_order.get(x.get("severity", "low"), 0))

            return issues[:limit]

        finally:
            conn.close()

    def surface_forgotten_knowledge(
        self, context: dict[str, Any] | None = None, days_threshold: int = 14, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Surface relevant but unaccessed memories.

        Args:
            context: Current context analysis
            days_threshold: Days since last access threshold (default: 14)
            limit: Maximum results (default: 5)

        Returns:
            List of forgotten but relevant memories
        """
        conn = self._get_db_connection()

        try:
            threshold_time = int(
                (datetime.now() - timedelta(days=days_threshold)).timestamp() * 1000
            )

            # Build query for high-importance, unaccessed memories
            query = """
                SELECT id, type, content, project, file_path, entities,
                       importance_score, last_accessed, access_count
                FROM memories
                WHERE importance_score >= 0.6
                  AND (last_accessed < ? OR last_accessed IS NULL)
                  AND archived = 0
            """
            params: list[Any] = [threshold_time]

            # Filter by context project if available
            if context and context.get("active_projects"):
                project_placeholders = ",".join("?" * len(context["active_projects"]))
                query += f" AND project IN ({project_placeholders})"
                params.extend(context["active_projects"])

            query += " ORDER BY importance_score DESC LIMIT ?"
            params.append(limit * 2)

            cursor = conn.execute(query, params)
            memories = [dict(row) for row in cursor.fetchall()]

            # Score by relevance to context
            results = []
            for memory in memories:
                relevance = self._calculate_context_relevance(memory, context)

                # Calculate days since access
                if memory.get("last_accessed"):
                    last_accessed = datetime.fromtimestamp(memory["last_accessed"] / 1000)
                    days_since = (datetime.now() - last_accessed).days
                else:
                    days_since = 9999

                results.append(
                    {
                        "type": "forgotten_knowledge",
                        "memory_id": memory["id"],
                        "content_preview": memory["content"][:200] + "..."
                        if len(memory.get("content", "")) > 200
                        else memory.get("content", ""),
                        "project": memory.get("project"),
                        "importance_score": memory.get("importance_score", 0),
                        "days_since_access": days_since,
                        "relevance_to_context": round(relevance, 3),
                        "reason": f"Important memory ({memory.get('importance_score', 0):.2f}) not accessed in {days_since} days",
                    }
                )

            # Sort by relevance and return
            results.sort(key=lambda x: -x["relevance_to_context"])
            return results[:limit]

        finally:
            conn.close()

    def recommend_best_practices(
        self, context: dict[str, Any] | None = None, limit: int = 3
    ) -> list[dict[str, Any]]:
        """
        Recommend best practices from historical patterns.

        Args:
            context: Current context analysis
            limit: Maximum recommendations (default: 3)

        Returns:
            List of best practice recommendations
        """
        conn = self._get_db_connection()

        try:
            recommendations = []

            # Find high-importance decisions/insights related to context
            query = """
                SELECT id, type, content, project, tags, importance_score
                FROM memories
                WHERE type IN ('decision', 'insight', 'note')
                  AND importance_score >= 0.7
                  AND archived = 0
            """
            params: list[Any] = []

            if context and context.get("primary_project"):
                query += " AND project = ?"
                params.append(context["primary_project"])

            query += " ORDER BY importance_score DESC, timestamp DESC LIMIT 20"

            cursor = conn.execute(query, params)
            memories = [dict(row) for row in cursor.fetchall()]

            # Find patterns that match current focus
            focus = context.get("current_focus", "") if context else ""
            focus_topic = focus.split(":")[-1] if ":" in focus else ""

            for memory in memories:
                content_lower = memory.get("content", "").lower()

                # Check if relevant to focus
                relevance_score = 0.0

                if focus_topic and focus_topic.lower() in content_lower:
                    relevance_score = 0.8
                elif context and context.get("context_type"):
                    if context["context_type"] in content_lower:
                        relevance_score = 0.5

                if relevance_score > 0:
                    recommendations.append(
                        {
                            "type": "best_practice",
                            "memory_id": memory["id"],
                            "content_preview": memory["content"][:200] + "..."
                            if len(memory.get("content", "")) > 200
                            else memory.get("content", ""),
                            "memory_type": memory.get("type"),
                            "relevance_score": relevance_score,
                            "priority": int(relevance_score * 10),
                            "reason": f"Related {memory.get('type', 'insight')} from past work",
                        }
                    )

            recommendations.sort(key=lambda x: -x["relevance_score"])
            return recommendations[:limit]

        finally:
            conn.close()

    def _get_forgotten_knowledge_suggestions(
        self, context: dict[str, Any] | None, limit: int = 2
    ) -> list[dict[str, Any]]:
        """Get suggestions based on forgotten knowledge"""
        forgotten = self.surface_forgotten_knowledge(context, limit=limit)

        suggestions = []
        for item in forgotten:
            suggestions.append(
                {
                    "type": "forgotten_knowledge",
                    "title": "Review forgotten important memory",
                    "description": item["content_preview"],
                    "memory_id": item["memory_id"],
                    "priority": 7,
                    "action": "review",
                    "reason": item["reason"],
                }
            )

        return suggestions

    def _get_pattern_based_suggestions(
        self, context: dict[str, Any] | None, limit: int = 2
    ) -> list[dict[str, Any]]:
        """Get suggestions based on detected patterns"""
        if not context or not context.get("active"):
            return []

        suggestions = []

        # Suggest based on context type
        context_type = context.get("context_type")

        if context_type == "debugging":
            suggestions.append(
                {
                    "type": "pattern_suggestion",
                    "title": "Check error patterns",
                    "description": "You appear to be debugging. Consider checking past error resolutions for similar issues.",
                    "priority": 8,
                    "action": "search_errors",
                    "reason": "Debugging context detected",
                }
            )

        elif context_type == "coding":
            if context.get("active_entities"):
                suggestions.append(
                    {
                        "type": "pattern_suggestion",
                        "title": "Review related code patterns",
                        "description": f"Working with: {', '.join(context['active_entities'][:3])}. Check past implementations for patterns.",
                        "priority": 6,
                        "action": "search_implementations",
                        "reason": "Active entities detected",
                    }
                )

        return suggestions[:limit]

    def _get_issue_suggestions(
        self, context: dict[str, Any] | None, limit: int = 2
    ) -> list[dict[str, Any]]:
        """Get suggestions based on detected issues"""
        project = context.get("primary_project") if context else None
        issues = self.detect_potential_issues(project=project, limit=limit)

        suggestions = []
        for issue in issues:
            priority = 9 if issue.get("severity") == "high" else 6
            suggestions.append(
                {
                    "type": "issue_suggestion",
                    "title": issue.get("title", "Potential issue detected"),
                    "description": issue.get("description", ""),
                    "priority": priority,
                    "action": "investigate",
                    "reason": issue.get("reason", "Pattern analysis"),
                }
            )

        return suggestions[:limit]

    def _get_best_practice_suggestions(
        self, context: dict[str, Any] | None, limit: int = 2
    ) -> list[dict[str, Any]]:
        """Get suggestions based on best practices"""
        practices = self.recommend_best_practices(context, limit=limit)

        suggestions = []
        for practice in practices:
            suggestions.append(
                {
                    "type": "best_practice",
                    "title": "Relevant past insight",
                    "description": practice["content_preview"],
                    "memory_id": practice.get("memory_id"),
                    "priority": 5,
                    "action": "review",
                    "reason": practice.get("reason", "Historical pattern"),
                }
            )

        return suggestions[:limit]

    def _find_unresolved_todos(
        self, conn: sqlite3.Connection, project: str | None
    ) -> list[dict[str, Any]]:
        """Find unresolved TODO items"""
        query = """
            SELECT id, content, project, timestamp
            FROM memories
            WHERE (content LIKE '%TODO%' OR content LIKE '%FIXME%' OR content LIKE '%HACK%')
              AND archived = 0
        """
        params: list[Any] = []

        if project:
            query += " AND project = ?"
            params.append(project)

        query += " ORDER BY timestamp DESC LIMIT 10"

        cursor = conn.execute(query, params)
        todos = [dict(row) for row in cursor.fetchall()]

        issues = []
        for todo in todos:
            content = todo.get("content", "")

            # Extract the TODO line
            for line in content.split("\n"):
                line_lower = line.lower()
                if "todo" in line_lower or "fixme" in line_lower or "hack" in line_lower:
                    issues.append(
                        {
                            "type": "unresolved_todo",
                            "title": "Unresolved TODO",
                            "description": line.strip()[:100],
                            "memory_id": todo["id"],
                            "project": todo.get("project"),
                            "severity": "medium",
                            "reason": "Found in memory content",
                        }
                    )
                    break

        return issues[:3]

    def _find_repeated_errors(
        self, conn: sqlite3.Connection, project: str | None
    ) -> list[dict[str, Any]]:
        """Find repeated error patterns"""
        week_ago = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)

        query = """
            SELECT content, COUNT(*) as count
            FROM memories
            WHERE (content LIKE '%error%' OR content LIKE '%Error%' OR content LIKE '%exception%')
              AND timestamp > ?
              AND archived = 0
        """
        params: list[Any] = [week_ago]

        if project:
            query += " AND project = ?"
            params.append(project)

        query += " GROUP BY content_hash HAVING count > 1 LIMIT 5"

        cursor = conn.execute(query, params)
        errors = [dict(row) for row in cursor.fetchall()]

        issues = []
        for error in errors:
            issues.append(
                {
                    "type": "repeated_error",
                    "title": f"Repeated error ({error['count']} times)",
                    "description": error["content"][:100] + "...",
                    "severity": "high" if error["count"] >= 3 else "medium",
                    "reason": "Error occurred multiple times this week",
                }
            )

        return issues[:2]

    def _find_stale_important_memories(
        self, conn: sqlite3.Connection, project: str | None
    ) -> list[dict[str, Any]]:
        """Find important memories that haven't been accessed"""
        month_ago = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)

        query = """
            SELECT id, content, importance_score
            FROM memories
            WHERE importance_score >= 0.8
              AND (last_accessed < ? OR last_accessed IS NULL)
              AND archived = 0
        """
        params: list[Any] = [month_ago]

        if project:
            query += " AND project = ?"
            params.append(project)

        query += " ORDER BY importance_score DESC LIMIT 3"

        cursor = conn.execute(query, params)
        stale = [dict(row) for row in cursor.fetchall()]

        issues = []
        for memory in stale:
            issues.append(
                {
                    "type": "stale_important_memory",
                    "title": "Important memory needs review",
                    "description": memory["content"][:100] + "...",
                    "memory_id": memory["id"],
                    "severity": "low",
                    "reason": f"High importance ({memory['importance_score']:.2f}) but not accessed in 30+ days",
                }
            )

        return issues

    def _calculate_context_relevance(
        self, memory: dict[str, Any], context: dict[str, Any] | None
    ) -> float:
        """Calculate relevance of memory to context"""
        if not context:
            return 0.5

        score = 0.0

        # Project match
        if memory.get("project") in context.get("active_projects", []):
            score += 0.4

        # Entity overlap
        if memory.get("entities") and context.get("active_entities"):
            try:
                memory_entities = set(json.loads(memory["entities"]))
                context_entities = set(context["active_entities"])
                overlap = len(memory_entities & context_entities)
                score += min(0.4, overlap * 0.15)
            except (json.JSONDecodeError, TypeError):
                pass

        # Importance factor
        score += memory.get("importance_score", 0.5) * 0.2

        return score


# Factory function
def get_suggestion_engine(db_path: str | None = None) -> SuggestionEngine:
    """Get a suggestion engine instance."""
    return SuggestionEngine(db_path=db_path)
