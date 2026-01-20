"""
Importance Scoring Service
Calculates memory importance based on multiple factors
"""

import logging
import math
import sqlite3
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class ImportanceScoringService:
    """Service for calculating memory importance scores"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
        self.logger = logging.getLogger("ImportanceScoringService")

    def calculate_importance(self, memory: dict[str, Any]) -> float:
        """
        Calculate importance score for a memory (0-1)

        Factors:
        - Content uniqueness (TF-IDF)
        - Source credibility
        - User engagement (access count)
        - Temporal relevance (recency)
        - Context signals (tags, project)
        """

        scores = []
        weights = []

        # 1. Content Uniqueness (30%)
        uniqueness = self._calculate_uniqueness(
            memory.get("content", ""), memory.get("type", "unknown")
        )
        scores.append(uniqueness)
        weights.append(0.30)

        # 2. Source Credibility (20%)
        source_score = self._calculate_source_score(
            memory.get("source", "unknown"), memory.get("type", "unknown")
        )
        scores.append(source_score)
        weights.append(0.20)

        # 3. User Engagement (25%)
        # Ensure access_count and created_at have defaults if missing
        access_count = memory.get("access_count", 0) or 0
        created_at = (
            memory.get("created_at", datetime.now().timestamp()) or datetime.now().timestamp()
        )

        engagement = self._calculate_engagement(access_count, created_at)
        scores.append(engagement)
        weights.append(0.25)

        # 4. Temporal Relevance (15%)
        timestamp = (
            memory.get("timestamp", datetime.now().timestamp()) or datetime.now().timestamp()
        )
        recency = self._calculate_recency(timestamp)
        scores.append(recency)
        weights.append(0.15)

        # 5. Context Signals (10%)
        context_score = self._calculate_context_score(memory)
        scores.append(context_score)
        weights.append(0.10)

        # Weighted average
        final_score = sum(s * w for s, w in zip(scores, weights, strict=False))

        return max(0.0, min(1.0, final_score))

    def _calculate_uniqueness(self, content: str, memory_type: str) -> float:
        """Calculate content uniqueness using TF-IDF"""
        if not content:
            return 0.5

        try:
            # Get similar memories
            cursor = self.conn.execute(
                "SELECT content FROM memories WHERE type = ? AND archived = 0 ORDER BY timestamp DESC LIMIT 100",
                (memory_type,),
            )

            corpus = [row["content"] for row in cursor.fetchall() if row["content"]]

            # If not enough data, return default
            if len(corpus) < 2:
                return 0.8  # Default for new types

            corpus.append(content)
            vectorizer = TfidfVectorizer(max_features=100, stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(corpus)

            # Get uniqueness of the last document (our memory)
            # We can approximate uniqueness as 1 - average similarity to others
            # But here we'll use mean term score as a proxy for "information density"
            # or simply use the provided logic of mean vector value
            last_vector = tfidf_matrix[-1].toarray()[0]
            uniqueness = np.mean(last_vector)

            return min(1.0, uniqueness * 2)  # Scale up

        except Exception as e:
            self.logger.warning(f"Error calculating uniqueness: {e}")
            return 0.5  # Default on error

    def _calculate_source_score(self, source: str, memory_type: str) -> float:
        """Calculate score based on source credibility"""

        # Source credibility mapping
        source_scores = {
            "manual": 0.8,  # Explicitly saved by user
            "ide": 0.7,  # From IDE, likely important
            "terminal": 0.6,  # From terminal, may be noise
            "unknown": 0.5,
        }

        # Type importance mapping
        type_scores = {
            "code": 0.9,
            "conversation": 0.8,
            "event": 0.7,
            "note": 0.7,
            "command": 0.5,
            "unknown": 0.5,
        }

        source_base = source_scores.get(source, 0.5)
        type_base = type_scores.get(memory_type, 0.5)

        return (source_base + type_base) / 2

    def _calculate_engagement(self, access_count: int, created_at: float) -> float:
        """Calculate score based on user engagement"""

        if access_count == 0:
            return 0.2

        # Age in days
        age_days = (datetime.now().timestamp() - created_at) / 86400

        if age_days <= 0:
            return 0.5  # Too new to judge

        # Access frequency (accesses per day)
        frequency = access_count / max(1, age_days)

        # Normalize (assuming 1 access/day is high)
        engagement = min(1.0, frequency)

        # Boost for multiple accesses
        if access_count >= 5:
            engagement = min(1.0, engagement * 1.2)

        return engagement

    def _calculate_recency(self, timestamp: float) -> float:
        """Calculate score based on recency"""

        # Handle timestamp in milliseconds
        if timestamp > 1e12:  # Likely milliseconds
            timestamp = timestamp / 1000

        now = datetime.now().timestamp()
        age_seconds = now - timestamp

        # Bounds check to prevent overflow
        if age_seconds < 0:
            return 1.0  # Future timestamp, treat as very recent

        age_days = age_seconds / 86400

        # Cap age to prevent overflow
        if age_days > 365:
            return 0.01  # Very old

        # Exponential decay: recent = high score
        # Half-life of 7 days
        decay_rate = math.log(2) / 7
        recency = math.exp(-decay_rate * age_days)

        return min(1.0, max(0.0, recency))

    def _calculate_context_score(self, memory: dict[str, Any]) -> float:
        """Calculate score based on context richness"""

        score = 0.5  # Base score

        # Has project
        if memory.get("project"):
            score += 0.15

        # Has file path
        if memory.get("file_path"):
            score += 0.15

        # Has tags
        if memory.get("tags"):
            tags = memory["tags"]
            if isinstance(tags, str):
                # Try to check if it's a non-empty string representing a list or just a string
                if len(tags) > 2:  # '[]' is 2 chars
                    score += 0.1
            elif isinstance(tags, list):
                tag_count = len(tags)
                score += min(0.2, tag_count * 0.05)

        return min(1.0, score)

    def batch_calculate(self, memory_ids: list[str]) -> dict[str, float]:
        """Calculate importance for multiple memories"""

        results = {}

        for memory_id in memory_ids:
            cursor = self.conn.execute(
                """
                SELECT id, type, source, content, timestamp, access_count,
                       created_at, project, file_path, tags
                FROM memories
                WHERE id = ?
                """,
                (memory_id,),
            )

            row = cursor.fetchone()
            if row:
                memory = dict(row)
                if memory.get("tags") and isinstance(memory["tags"], str):
                    import json

                    try:
                        memory["tags"] = json.loads(memory["tags"])
                    except:
                        memory["tags"] = []

                importance = self.calculate_importance(memory)
                results[memory_id] = importance

        return results
