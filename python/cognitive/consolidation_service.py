"""
Consolidation Service
Merges, deduplicates, and creates abstractions from memories
"""

import contextlib
import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import textdistance
except ImportError:
    textdistance = None


class ConsolidationService:
    """Consolidates, merges, and deduplicates memories"""

    def __init__(self, db_path: str | None = None):
        """
        Initialize the consolidation service.

        Args:
            db_path: Path to SQLite database
        """
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "data" / "memory.db")

        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def find_duplicates(
        self, similarity_threshold: float = 0.85, project: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Find duplicate or near-duplicate memories.

        Args:
            similarity_threshold: Minimum similarity to consider duplicate (default: 0.85)
            project: Optional project filter
            limit: Maximum duplicate groups to return (default: 50)

        Returns:
            List of duplicate groups with similarity scores
        """
        conn = self._get_db_connection()

        try:
            # First, find exact duplicates by hash
            exact_duplicates = self._find_exact_duplicates(conn, project)

            # Then find near-duplicates using text similarity
            if textdistance is not None:
                near_duplicates = self._find_near_duplicates(conn, project, similarity_threshold)
            else:
                near_duplicates = []

            # Combine and deduplicate results
            all_duplicates = exact_duplicates + near_duplicates

            # Sort by group size and similarity
            all_duplicates.sort(key=lambda x: (-x.get("count", 0), -x.get("similarity", 0)))

            return all_duplicates[:limit]

        finally:
            conn.close()

    def merge_memories(self, memory_ids: list[str], strategy: str = "keep_best") -> dict[str, Any]:
        """
        Merge multiple memories into one.

        Args:
            memory_ids: List of memory IDs to merge
            strategy: Merge strategy - 'keep_best', 'combine', or 'summarize'

        Returns:
            Merge result with kept/archived memory IDs
        """
        if len(memory_ids) < 2:
            return {"error": "Need at least 2 memories to merge"}

        conn = self._get_db_connection()

        try:
            # Get all memories
            placeholders = ",".join("?" * len(memory_ids))
            cursor = conn.execute(
                f"""
                SELECT id, type, content, project, file_path, tags, entities,
                       importance_score, access_count, timestamp
                FROM memories
                WHERE id IN ({placeholders}) AND archived = 0
            """,
                tuple(memory_ids),
            )

            memories = [dict(row) for row in cursor.fetchall()]

            if len(memories) < 2:
                return {"error": "Could not find enough memories to merge"}

            # Execute strategy
            if strategy == "keep_best":
                result = self._merge_keep_best(conn, memories)
            elif strategy == "combine":
                result = self._merge_combine(conn, memories)
            else:
                return {"error": f"Unknown strategy: {strategy}"}

            conn.commit()
            return result

        except Exception as e:
            conn.rollback()
            return {"error": str(e)}
        finally:
            conn.close()

    def create_abstraction(
        self, memory_ids: list[str], title: str, summary: str | None = None
    ) -> dict[str, Any]:
        """
        Create a higher-level abstraction from multiple memories.

        Args:
            memory_ids: Source memory IDs
            title: Title for the abstraction
            summary: Optional summary (auto-generated if not provided)

        Returns:
            Created abstraction details
        """
        if not memory_ids:
            return {"error": "No memory IDs provided"}

        conn = self._get_db_connection()

        try:
            # Get source memories
            placeholders = ",".join("?" * len(memory_ids))
            cursor = conn.execute(
                f"""
                SELECT id, type, content, project, entities, importance_score
                FROM memories
                WHERE id IN ({placeholders}) AND archived = 0
            """,
                tuple(memory_ids),
            )

            memories = [dict(row) for row in cursor.fetchall()]

            if not memories:
                return {"error": "No valid memories found"}

            # Generate summary if not provided
            if not summary:
                summary = self._generate_abstraction_summary(memories)

            # Collect entities
            all_entities: set[str] = set()
            for memory in memories:
                if memory.get("entities"):
                    with contextlib.suppress(json.JSONDecodeError, TypeError):
                        all_entities.update(json.loads(memory["entities"]))

            # Get project (most common)
            projects = [m["project"] for m in memories if m.get("project")]
            project = max(set(projects), key=projects.count) if projects else None

            # Calculate importance (average + boost)
            avg_importance = sum(m.get("importance_score", 0.5) for m in memories) / len(memories)
            abstraction_importance = min(1.0, avg_importance + 0.1)  # Slight boost

            # Create abstraction memory
            import uuid

            abstraction_id = str(uuid.uuid4())
            now = int(datetime.now(UTC).timestamp() * 1000)

            content = f"# {title}\n\n{summary}\n\n---\nAbstraction of {len(memories)} memories."
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            conn.execute(
                """
                INSERT INTO memories (
                    id, tier, type, source, content, content_hash,
                    timestamp, project, entities, importance_score,
                    created_at, archived
                ) VALUES (?, 'long', 'insight', 'consolidation', ?, ?, ?, ?, ?, ?, ?, 0)
            """,
                (
                    abstraction_id,
                    content,
                    content_hash,
                    now,
                    project,
                    json.dumps(list(all_entities)) if all_entities else None,
                    abstraction_importance,
                    now,
                ),
            )

            conn.commit()

            return {
                "abstraction_id": abstraction_id,
                "title": title,
                "summary": summary,
                "source_count": len(memories),
                "source_ids": memory_ids,
                "entities": list(all_entities),
                "importance_score": abstraction_importance,
            }

        except Exception as e:
            conn.rollback()
            return {"error": str(e)}
        finally:
            conn.close()

    def garbage_collect(
        self, max_age_days: int = 90, min_importance: float = 0.3, dry_run: bool = True
    ) -> dict[str, Any]:
        """
        Identify and optionally archive low-value memories.

        Args:
            max_age_days: Maximum age for low-importance memories (default: 90)
            min_importance: Minimum importance to keep (default: 0.3)
            dry_run: If True, only report without archiving (default: True)

        Returns:
            Garbage collection results
        """
        conn = self._get_db_connection()

        try:
            cutoff = int(
                (datetime.now(UTC) - __import__("datetime").timedelta(days=max_age_days)).timestamp()
                * 1000
            )

            # Find candidates for archival
            cursor = conn.execute(
                """
                SELECT id, content, project, importance_score, access_count, timestamp
                FROM memories
                WHERE importance_score < ?
                  AND timestamp < ?
                  AND access_count < 3
                  AND archived = 0
                ORDER BY importance_score ASC, timestamp ASC
                LIMIT 100
            """,
                (min_importance, cutoff),
            )

            candidates = [dict(row) for row in cursor.fetchall()]

            if not dry_run and candidates:
                # Archive candidates
                ids = [c["id"] for c in candidates]
                placeholders = ",".join("?" * len(ids))
                conn.execute(
                    f"""
                    UPDATE memories
                    SET archived = 1
                    WHERE id IN ({placeholders})
                """,
                    tuple(ids),
                )
                conn.commit()

            return {
                "dry_run": dry_run,
                "candidates_found": len(candidates),
                "archived": 0 if dry_run else len(candidates),
                "criteria": {
                    "max_age_days": max_age_days,
                    "min_importance": min_importance,
                    "min_access_count": 3,
                },
                "samples": candidates[:5],  # Show first 5
            }

        finally:
            conn.close()

    def get_consolidation_stats(self) -> dict[str, Any]:
        """
        Get statistics about memory consolidation potential.

        Returns:
            Consolidation statistics
        """
        conn = self._get_db_connection()

        try:
            # Total active memories
            cursor = conn.execute("SELECT COUNT(*) as count FROM memories WHERE archived = 0")
            total_active = cursor.fetchone()["count"]

            # Archived memories
            cursor = conn.execute("SELECT COUNT(*) as count FROM memories WHERE archived = 1")
            total_archived = cursor.fetchone()["count"]

            # Potential exact duplicates
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM (
                    SELECT content_hash, COUNT(*) as c
                    FROM memories
                    WHERE archived = 0
                    GROUP BY content_hash
                    HAVING c > 1
                )
            """)
            exact_duplicate_groups = cursor.fetchone()["count"]

            # Low importance candidates
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM memories
                WHERE importance_score < 0.3
                  AND access_count < 2
                  AND archived = 0
            """)
            low_quality_count = cursor.fetchone()["count"]

            # Memory tier distribution
            cursor = conn.execute("""
                SELECT tier, COUNT(*) as count
                FROM memories
                WHERE archived = 0
                GROUP BY tier
            """)
            tier_distribution = {row["tier"]: row["count"] for row in cursor.fetchall()}

            return {
                "total_active": total_active,
                "total_archived": total_archived,
                "exact_duplicate_groups": exact_duplicate_groups,
                "low_quality_candidates": low_quality_count,
                "tier_distribution": tier_distribution,
                "consolidation_potential": {
                    "duplicates": exact_duplicate_groups,
                    "low_quality": low_quality_count,
                    "total_reduction": exact_duplicate_groups + low_quality_count,
                },
            }

        finally:
            conn.close()

    def _find_exact_duplicates(
        self, conn: sqlite3.Connection, project: str | None
    ) -> list[dict[str, Any]]:
        """Find exact duplicates by content hash"""
        query = """
            SELECT content_hash, GROUP_CONCAT(id) as ids, COUNT(*) as count
            FROM memories
            WHERE archived = 0
        """
        params: list[Any] = []

        if project:
            query += " AND project = ?"
            params.append(project)

        query += " GROUP BY content_hash HAVING count > 1 LIMIT 20"

        cursor = conn.execute(query, params)

        duplicates = []
        for row in cursor.fetchall():
            ids = row["ids"].split(",")
            duplicates.append(
                {
                    "type": "exact_duplicate",
                    "content_hash": row["content_hash"],
                    "count": row["count"],
                    "memory_ids": ids,
                    "similarity": 1.0,
                }
            )

        return duplicates

    def _find_near_duplicates(
        self, conn: sqlite3.Connection, project: str | None, threshold: float
    ) -> list[dict[str, Any]]:
        """Find near-duplicates using text similarity"""
        query = """
            SELECT id, content
            FROM memories
            WHERE archived = 0
        """
        params: list[Any] = []

        if project:
            query += " AND project = ?"
            params.append(project)

        query += " ORDER BY timestamp DESC LIMIT 200"  # Limit for performance

        cursor = conn.execute(query, params)
        memories = [(row["id"], row["content"]) for row in cursor.fetchall()]

        # Compare pairs
        near_duplicates = []
        checked_pairs: set[tuple[str, str]] = set()

        for i, (id1, content1) in enumerate(memories):
            for id2, content2 in memories[i + 1 :]:
                pair = tuple(sorted([id1, id2]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                # Quick length check
                len_ratio = len(content1) / max(len(content2), 1)
                if len_ratio < 0.5 or len_ratio > 2:
                    continue

                # Calculate similarity
                similarity = textdistance.jaro_winkler.normalized_similarity(
                    content1[:500],
                    content2[:500],  # Limit for performance
                )

                if similarity >= threshold:
                    near_duplicates.append(
                        {
                            "type": "near_duplicate",
                            "memory_ids": [id1, id2],
                            "count": 2,
                            "similarity": round(similarity, 4),
                        }
                    )

        return near_duplicates[:20]  # Limit results

    def _merge_keep_best(
        self, conn: sqlite3.Connection, memories: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Keep the best memory and archive others"""
        # Score memories
        scored = []
        for memory in memories:
            score = (
                memory.get("importance_score", 0.5) * 0.4
                + min(memory.get("access_count", 0) / 10, 1) * 0.3
                + len(memory.get("content", "")) / 10000 * 0.3
            )
            scored.append((memory, score))

        scored.sort(key=lambda x: -x[1])

        keeper = scored[0][0]
        to_archive = [s[0]["id"] for s in scored[1:]]

        # Archive duplicates
        if to_archive:
            placeholders = ",".join("?" * len(to_archive))
            conn.execute(
                f"""
                UPDATE memories
                SET archived = 1
                WHERE id IN ({placeholders})
            """,
                tuple(to_archive),
            )

        return {
            "strategy": "keep_best",
            "kept_id": keeper["id"],
            "archived_ids": to_archive,
            "archived_count": len(to_archive),
        }

    def _merge_combine(
        self, conn: sqlite3.Connection, memories: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Combine memories into one new memory"""
        import uuid

        # Combine content
        combined_content = "# Combined Memory\n\n"
        all_entities: set[str] = set()
        all_tags: set[str] = set()

        for memory in memories:
            combined_content += f"---\n{memory.get('content', '')}\n"

            if memory.get("entities"):
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    all_entities.update(json.loads(memory["entities"]))

            if memory.get("tags"):
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    all_tags.update(json.loads(memory["tags"]))

        # Get best metadata
        project = (
            max(
                [m["project"] for m in memories if m.get("project")],
                key=lambda x: sum(1 for m in memories if m.get("project") == x),
                default=None,
            )
            if any(m.get("project") for m in memories)
            else None
        )

        importance = max(m.get("importance_score", 0.5) for m in memories)

        # Create new memory
        new_id = str(uuid.uuid4())
        now = int(datetime.now(UTC).timestamp() * 1000)
        content_hash = hashlib.sha256(combined_content.encode()).hexdigest()

        conn.execute(
            """
            INSERT INTO memories (
                id, tier, type, source, content, content_hash,
                timestamp, project, tags, entities, importance_score,
                created_at, archived
            ) VALUES (?, 'working', 'note', 'consolidation', ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
            (
                new_id,
                combined_content,
                content_hash,
                now,
                project,
                json.dumps(list(all_tags)) if all_tags else None,
                json.dumps(list(all_entities)) if all_entities else None,
                importance,
                now,
            ),
        )

        # Archive originals
        original_ids = [m["id"] for m in memories]
        placeholders = ",".join("?" * len(original_ids))
        conn.execute(
            f"""
            UPDATE memories
            SET archived = 1
            WHERE id IN ({placeholders})
        """,
            tuple(original_ids),
        )

        return {
            "strategy": "combine",
            "new_id": new_id,
            "archived_ids": original_ids,
            "archived_count": len(original_ids),
        }

    def _generate_abstraction_summary(self, memories: list[dict[str, Any]]) -> str:
        """Generate a summary for abstraction"""
        # Simple summary based on content
        types = {m.get("type", "unknown") for m in memories}
        projects = {m.get("project") for m in memories if m.get("project")}

        summary = f"This abstraction consolidates {len(memories)} memories"

        if types:
            summary += f" of types: {', '.join(types)}"

        if projects:
            summary += f" from projects: {', '.join(projects)}"

        summary += "."

        return summary


# Factory function
def get_consolidation_service(db_path: str | None = None) -> ConsolidationService:
    """Get a consolidation service instance."""
    return ConsolidationService(db_path=db_path)
