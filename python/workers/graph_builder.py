"""
Graph Builder Worker
Builds relationships between entities based on co-occurrence
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from collections import defaultdict
from typing import Any

from workers.base_worker import BaseWorker


class GraphBuilderWorker(BaseWorker):
    """Worker that builds entity relationship graph"""

    def __init__(self):
        super().__init__("GraphBuilder")

    def process(self) -> dict[str, Any]:
        """Build entity relationships"""

        conn = self.get_db_connection()

        try:
            # Get all memory-entity relationships
            cursor = conn.execute(
                """
                SELECT memory_id, entity_id, relevance
                FROM memory_entities
                ORDER BY memory_id
                """
            )

            memory_entities = cursor.fetchall()

            if not memory_entities:
                self.logger.info("No entities to build graph from")
                return {"processed": 0, "skipped": 0, "errors": 0}

            # Group by memory
            memory_map = defaultdict(list)
            for row in memory_entities:
                memory_map[row["memory_id"]].append(
                    {"entity_id": row["entity_id"], "relevance": row["relevance"]}
                )

            self.logger.info(f"Building graph from {len(memory_map)} memories...")

            # Build co-occurrence relationships
            relationships = defaultdict(lambda: {"count": 0, "strength": 0.0})

            for _memory_id, entities in memory_map.items():
                # Create relationships between all entity pairs in this memory
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i + 1 :]:
                        # Sort to ensure consistent ordering
                        pair = tuple(sorted([entity1["entity_id"], entity2["entity_id"]]))

                        # Co-occurrence strength based on both relevances
                        strength = (entity1["relevance"] + entity2["relevance"]) / 2

                        relationships[pair]["count"] += 1
                        relationships[pair]["strength"] += strength

            # Insert/update relationships
            now = int(datetime.now(UTC).timestamp())
            processed = 0

            for (source_id, target_id), data in relationships.items():
                # Average strength
                avg_strength = data["strength"] / data["count"]

                # Only create relationship if co-occurred multiple times
                if data["count"] >= 2:
                    # Check if relationship exists
                    existing = conn.execute(
                        """
                        SELECT strength FROM entity_relationships
                        WHERE source_id = ?  AND target_id = ?  AND type = 'related_to'
                        """,
                        (source_id, target_id),
                    ).fetchone()

                    if existing:
                        # Update with weighted average
                        new_strength = (existing["strength"] + avg_strength) / 2
                        conn.execute(
                            """
                            UPDATE entity_relationships
                            SET strength = ?, updated_at = ?
                            WHERE source_id = ? AND target_id = ?  AND type = 'related_to'
                            """,
                            (new_strength, now, source_id, target_id),
                        )
                    else:
                        # Insert new
                        conn.execute(
                            """
                            INSERT INTO entity_relationships
                            (source_id, target_id, type, strength, created_at, updated_at)
                            VALUES (?, ?, 'related_to', ?, ?, ?)
                            """,
                            (source_id, target_id, avg_strength, now, now),
                        )

                    processed += 1

            conn.commit()

            self.logger.info(f"Built/updated {processed} entity relationships")

            return {
                "processed": processed,
                "skipped": 0,
                "errors": 0,
                "details": {
                    "total_relationships": len(relationships),
                    "strong_relationships": sum(
                        1 for d in relationships.values() if d["count"] >= 3
                    ),
                },
            }

        finally:
            conn.close()


if __name__ == "__main__":
    worker = GraphBuilderWorker()
    result = worker.run()
    print(f"Result: {result}")
