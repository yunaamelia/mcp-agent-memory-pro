"""
Auto-Tagger
Automatically tags memories using ML
"""

import json
import re
import sqlite3
from collections import Counter
from typing import Any


class AutoTagger:
    """ML-based automatic tagging"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection

        # Common programming concepts
        self.tech_keywords = {
            # Languages
            "python",
            "javascript",
            "typescript",
            "java",
            "rust",
            "go",
            "cpp",
            "csharp",
            # Frameworks
            "react",
            "vue",
            "angular",
            "django",
            "flask",
            "fastapi",
            "express",
            "nextjs",
            # Databases
            "postgres",
            "mysql",
            "mongodb",
            "redis",
            "sqlite",
            "elasticsearch",
            # Cloud
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "terraform",
            # Concepts
            "api",
            "rest",
            "graphql",
            "websocket",
            "authentication",
            "authorization",
            "database",
            "cache",
            "queue",
            "async",
            "sync",
            "test",
            "deploy",
            # Patterns
            "crud",
            "mvc",
            "microservice",
            "monolith",
            "serverless",
        }

        self.action_keywords = {
            "fix",
            "bug",
            "error",
            "issue",
            "todo",
            "implement",
            "refactor",
            "optimize",
            "improve",
            "update",
            "add",
            "remove",
            "delete",
        }

    def auto_tag_memory(self, memory: dict[str, Any]) -> list[str]:
        """Generate tags for a memory"""

        content = memory.get("content", "").lower()
        memory_type = memory.get("type", "")

        tags = set()

        # 1. Extract from content
        tags.update(self._extract_tech_tags(content))
        tags.update(self._extract_action_tags(content))

        # 2. Type-based tags
        if memory_type == "code":
            tags.add("code")
            tags.update(self._extract_code_tags(memory.get("content", "")))
        elif memory_type == "note":
            tags.add("note")
            if any(word in content for word in ["todo", "remember", "important"]):
                tags.add("action-item")
        elif memory_type == "command":
            tags.add("command")
            tags.add("cli")
        elif memory_type == "event":
            tags.add("event")
            if "error" in content or "failed" in content:
                tags.add("error")

        # 3. Project-based tags
        if memory.get("project"):
            tags.add(f"project:{memory['project']}")

        # 4. Language-based tags
        if memory.get("language"):
            tags.add(memory["language"])

        # 5. Learn from similar memories
        tags.update(self._learn_from_similar(memory))

        # Filter and limit
        filtered_tags = [tag for tag in tags if len(tag) > 2 and len(tag) < 30]

        return sorted(filtered_tags)[:10]  # Limit to 10 tags

    def _extract_tech_tags(self, content: str) -> set[str]:
        """Extract technology-related tags"""

        tags = set()

        for keyword in self.tech_keywords:
            if re.search(r"\b" + keyword + r"\b", content, re.IGNORECASE):
                tags.add(keyword)

        return tags

    def _extract_action_tags(self, content: str) -> set[str]:
        """Extract action-related tags"""

        tags = set()

        for keyword in self.action_keywords:
            if re.search(r"\b" + keyword + r"\b", content, re.IGNORECASE):
                tags.add(keyword)

        return tags

    def _extract_code_tags(self, code: str) -> set[str]:
        """Extract tags from code"""

        tags = set()

        # Function definitions
        if re.search(r"\b(function|def|async\s+def|const\s+\w+\s*=\s*\()", code):
            tags.add("function")

        # Class definitions
        if re.search(r"\bclass\s+\w+", code):
            tags.add("class")

        # Async code
        if re.search(r"\b(async|await)\b", code):
            tags.add("async")

        # Error handling
        if re.search(r"\b(try|catch|except|throw|raise)\b", code):
            tags.add("error-handling")

        # Database
        if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|query|find|create)\b", code, re.IGNORECASE):
            tags.add("database")

        # API
        if re.search(r"\b(fetch|axios|request|get|post|put|delete)\b", code):
            tags.add("api")

        return tags

    def _learn_from_similar(self, memory: dict[str, Any]) -> set[str]:
        """Learn tags from similar memories"""

        # Find similar memories
        cursor = self.conn.execute(
            """
            SELECT tags FROM memories
            WHERE type = ?
              AND project = ?
              AND tags IS NOT NULL
              AND tags != '[]'
              AND archived = 0
            LIMIT 10
        """,
            (memory.get("type"), memory.get("project")),
        )

        # Count tag occurrences
        tag_counter = Counter()

        for row in cursor.fetchall():
            try:
                tags = json.loads(row["tags"])
                if isinstance(tags, list):
                    tag_counter.update(tags)
            except Exception:
                pass

        # Return most common tags
        common_tags = {tag for tag, count in tag_counter.most_common(5) if count >= 2}

        return common_tags

    def batch_auto_tag(self, memory_ids: list[str]) -> dict[str, list[str]]:
        """Auto-tag multiple memories"""

        results = {}

        for memory_id in memory_ids:
            cursor = self.conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()

            if row:
                memory = dict(row)
                tags = self.auto_tag_memory(memory)
                results[memory_id] = tags

        return results
