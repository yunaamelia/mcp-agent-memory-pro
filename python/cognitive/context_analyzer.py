"""
Context Analyzer
Understands current work context and proactively recalls relevant memories
"""

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class ContextAnalyzer:
    """Analyzes current context and proactively recalls relevant memories"""

    def __init__(self, db_path: str | None = None):
        """
        Initialize the context analyzer.

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

    def analyze_current_context(
        self,
        recent_window_minutes: int = 30,
        project_hint: str | None = None,
        file_hint: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze recent activity to understand current context.

        Args:
            recent_window_minutes: Time window for recent activity (default: 30)
            project_hint: Optional project name to focus on
            file_hint: Optional file path to focus on

        Returns:
            Context analysis with active projects, entities, patterns
        """
        cutoff_time = int(
            (datetime.now() - timedelta(minutes=recent_window_minutes)).timestamp() * 1000
        )

        conn = self._get_db_connection()

        try:
            # Build query
            query = """
                SELECT id, type, project, file_path, tags, entities, content
                FROM memories
                WHERE timestamp > ? AND archived = 0
            """
            params: list[Any] = [cutoff_time]

            if project_hint:
                query += " AND project = ?"
                params.append(project_hint)

            if file_hint:
                query += " AND file_path LIKE ?"
                params.append(f"%{file_hint}%")

            query += " ORDER BY timestamp DESC LIMIT 50"

            cursor = conn.execute(query, params)
            recent_memories = [dict(row) for row in cursor.fetchall()]

            if not recent_memories:
                return {
                    "active": False,
                    "context_type": None,
                    "active_projects": [],
                    "active_entities": [],
                    "current_focus": None,
                    "recent_activity_count": 0,
                    "suggestions": [],
                }

            # Extract patterns
            projects: Counter[str] = Counter()
            entities_all: Counter[str] = Counter()
            types: Counter[str] = Counter()
            files: Counter[str] = Counter()

            for memory in recent_memories:
                if memory.get("project"):
                    projects[memory["project"]] += 1

                if memory.get("type"):
                    types[memory["type"]] += 1

                if memory.get("file_path"):
                    files[memory["file_path"]] += 1

                if memory.get("entities"):
                    try:
                        entity_list = json.loads(memory["entities"])
                        for entity in entity_list:
                            entities_all[entity] += 1
                    except (json.JSONDecodeError, TypeError):
                        pass

            # Determine primary project
            primary_project = projects.most_common(1)[0][0] if projects else None

            # Determine context type
            context_type = self._infer_context_type(types, recent_memories)

            # Get top entities
            top_entities = [e for e, _ in entities_all.most_common(10)]

            # Determine current focus
            current_focus = self._infer_focus(recent_memories, files, entities_all)

            return {
                "active": True,
                "context_type": context_type,
                "primary_project": primary_project,
                "active_projects": [p for p, _ in projects.most_common(3)],
                "active_entities": top_entities,
                "active_files": [f for f, _ in files.most_common(5)],
                "current_focus": current_focus,
                "recent_activity_count": len(recent_memories),
                "time_window_minutes": recent_window_minutes,
                "activity_types": dict(types.most_common(5)),
            }

        finally:
            conn.close()

    def recall_relevant_memories(
        self,
        context: dict[str, Any] | None = None,
        limit: int = 10,
        exclude_recent_minutes: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Recall memories relevant to current context.

        Args:
            context: Context analysis (if None, will analyze current context)
            limit: Maximum memories to return (default: 10)
            exclude_recent_minutes: Exclude memories from this window (default: 30)

        Returns:
            List of relevant memories with relevance scores
        """
        if context is None:
            context = self.analyze_current_context()

        if not context.get("active"):
            return []

        conn = self._get_db_connection()

        try:
            # Build query based on context
            conditions = []
            params: list[Any] = []

            # Match project
            if context.get("active_projects"):
                project_placeholders = ",".join("?" * len(context["active_projects"]))
                conditions.append(f"project IN ({project_placeholders})")
                params.extend(context["active_projects"])

            # Match entities (top 5)
            if context.get("active_entities"):
                entity_conditions = []
                for entity in context["active_entities"][:5]:
                    entity_conditions.append("entities LIKE ?")
                    params.append(f"%{entity}%")

                if entity_conditions:
                    conditions.append(f"({' OR '.join(entity_conditions)})")

            # Exclude very recent (already in context window)
            recent_cutoff = int(
                (datetime.now() - timedelta(minutes=exclude_recent_minutes)).timestamp() * 1000
            )
            conditions.append("timestamp < ?")
            params.append(recent_cutoff)

            # Only non-archived
            conditions.append("archived = 0")

            if not conditions:
                return []

            # Query with scoring hints
            query = f"""
                SELECT id, type, content, project, file_path, tags, entities,
                       timestamp, importance_score, access_count
                FROM memories
                WHERE {" AND ".join(conditions)}
                ORDER BY importance_score DESC, access_count DESC, timestamp DESC
                LIMIT ?
            """
            params.append(limit * 3)  # Get more for scoring

            cursor = conn.execute(query, params)
            memories = [dict(row) for row in cursor.fetchall()]

            # Calculate relevance scores
            scored_memories = []
            for memory in memories:
                relevance = self._calculate_relevance(memory, context)
                scored_memories.append(
                    {
                        **memory,
                        "relevance_score": round(relevance, 4),
                        "recall_reason": self._get_recall_reason(memory, context),
                    }
                )

            # Sort by relevance and limit
            scored_memories.sort(key=lambda x: x["relevance_score"], reverse=True)

            return scored_memories[:limit]

        finally:
            conn.close()

    def get_related_memories_for_entity(
        self, entity_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get memories related to a specific entity.

        Args:
            entity_name: Entity name to search for
            limit: Maximum results (default: 10)

        Returns:
            List of memories mentioning this entity
        """
        conn = self._get_db_connection()

        try:
            cursor = conn.execute(
                """
                SELECT m.id, m.type, m.content, m.project, m.file_path,
                       m.tags, m.entities, m.timestamp, m.importance_score
                FROM memories m
                WHERE m.entities LIKE ? AND m.archived = 0
                ORDER BY m.importance_score DESC, m.timestamp DESC
                LIMIT ?
            """,
                (f"%{entity_name}%", limit),
            )

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def _infer_context_type(self, types: Counter, recent_memories: list[dict]) -> str:
        """Infer what type of work is being done"""
        if not types:
            return "unknown"

        primary_type = types.most_common(1)[0][0]

        # Check content for patterns
        all_content = " ".join(m.get("content", "")[:200].lower() for m in recent_memories[:10])

        # Detect debugging
        error_keywords = ["error", "exception", "traceback", "failed", "bug", "fix"]
        if any(kw in all_content for kw in error_keywords):
            return "debugging"

        # Type-based inference
        context_map = {
            "code": "coding",
            "command": "system_admin",
            "conversation": "planning",
            "note": "documentation",
            "decision": "planning",
            "insight": "analysis",
        }

        return context_map.get(primary_type, "general")

    def _infer_focus(
        self, recent_memories: list[dict], files: Counter, entities: Counter
    ) -> str | None:
        """Infer current focus area"""
        if not recent_memories:
            return None

        # Check if focused on specific file
        if files:
            top_file = files.most_common(1)[0]
            if top_file[1] >= 3:  # Mentioned 3+ times
                return f"file:{top_file[0]}"

        # Check if focused on specific entity
        if entities:
            top_entity = entities.most_common(1)[0]
            if top_entity[1] >= 3:
                return f"entity:{top_entity[0]}"

        # Check content patterns
        recent_content = " ".join(m.get("content", "")[:200] for m in recent_memories[:5]).lower()

        focus_keywords = {
            "authentication": "auth",
            "login": "auth",
            "database": "database",
            "sql": "database",
            "api": "api",
            "endpoint": "api",
            "test": "testing",
            "spec": "testing",
            "deploy": "deployment",
            "docker": "deployment",
            "kubernetes": "deployment",
            "performance": "optimization",
            "memory": "optimization",
            "security": "security",
            "refactor": "refactoring",
        }

        for keyword, focus in focus_keywords.items():
            if keyword in recent_content:
                return f"topic:{focus}"

        return None

    def _calculate_relevance(self, memory: dict[str, Any], context: dict[str, Any]) -> float:
        """Calculate how relevant a memory is to current context"""
        score = 0.0
        max_score = 1.0

        # Project match (high weight: 0.35)
        if memory.get("project"):
            if memory["project"] == context.get("primary_project"):
                score += 0.35
            elif memory["project"] in context.get("active_projects", []):
                score += 0.2

        # Entity overlap (weight: 0.30)
        if memory.get("entities"):
            try:
                memory_entities = set(json.loads(memory["entities"]))
                context_entities = set(context.get("active_entities", []))
                if memory_entities and context_entities:
                    overlap = len(memory_entities & context_entities)
                    entity_score = min(0.30, overlap * 0.10)
                    score += entity_score
            except (json.JSONDecodeError, TypeError):
                pass

        # File proximity (weight: 0.15)
        if memory.get("file_path") and context.get("active_files"):
            if memory["file_path"] in context["active_files"]:
                score += 0.15
            else:
                # Check directory match
                for active_file in context["active_files"]:
                    if self._same_directory(memory["file_path"], active_file):
                        score += 0.08
                        break

        # Importance score (weight: 0.15)
        importance = memory.get("importance_score", 0.5)
        score += importance * 0.15

        # Access count bonus (weight: 0.05)
        access_normalized = min(1.0, memory.get("access_count", 0) / 10)
        score += access_normalized * 0.05

        return min(score, max_score)

    def _get_recall_reason(self, memory: dict[str, Any], context: dict[str, Any]) -> str:
        """Generate a human-readable reason for recalling this memory"""
        reasons = []

        if memory.get("project") == context.get("primary_project"):
            reasons.append(f"Same project: {memory['project']}")

        if memory.get("entities"):
            try:
                memory_entities = set(json.loads(memory["entities"]))
                context_entities = set(context.get("active_entities", []))
                overlap = memory_entities & context_entities
                if overlap:
                    reasons.append(f"Related entities: {', '.join(list(overlap)[:3])}")
            except (json.JSONDecodeError, TypeError):
                pass

        if memory.get("file_path") and context.get("active_files"):
            if memory["file_path"] in context["active_files"]:
                reasons.append(f"Same file: {memory['file_path']}")

        if memory.get("importance_score", 0) >= 0.7:
            reasons.append("High importance")

        return "; ".join(reasons) if reasons else "General relevance"

    def _same_directory(self, path1: str, path2: str) -> bool:
        """Check if two paths are in the same directory"""
        try:
            from pathlib import Path

            return Path(path1).parent == Path(path2).parent
        except Exception:
            return False


# Factory function
def get_context_analyzer(db_path: str | None = None) -> ContextAnalyzer:
    """Get a context analyzer instance."""
    return ContextAnalyzer(db_path=db_path)
