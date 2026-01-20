"""
Entity Extractor Worker
Extracts entities from memories and builds knowledge graph
"""

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from typing import Any

from config import BATCH_SIZE
from services.ner_service import NERService
from workers.base_worker import BaseWorker


class EntityExtractorWorker(BaseWorker):
    """Worker that extracts entities from memories"""

    def __init__(self):
        super().__init__("EntityExtractor")
        self.ner_service = NERService()

    def process(self) -> dict[str, Any]:
        """Process memories needing entity extraction"""

        conn = self.get_db_connection()

        try:
            # Get memories without entities
            cursor = conn.execute(
                """
                SELECT id, type, source, content, project, language, tags, file_path
                FROM memories
                WHERE archived = 0
                  AND (entities IS NULL OR entities = '[]')
                  AND timestamp > ?
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT ?
                """,
                (int((datetime.now(UTC) - timedelta(days=30)).timestamp() * 1000), BATCH_SIZE),
            )

            memories = cursor.fetchall()

            if not memories:
                self.logger.info("No memories need entity extraction")
                return {"processed": 0, "skipped": 0, "errors": 0}

            self.logger.info(f"Extracting entities from {len(memories)} memories...")

            processed = 0
            errors = 0
            total_entities = 0
            entity_counts = {}

            for memory in memories:
                try:
                    memory_dict = dict(memory)

                    # Parse tags
                    if memory_dict.get("tags"):
                        try:
                            memory_dict["tags"] = json.loads(memory_dict["tags"])
                        except:
                            memory_dict["tags"] = []

                    # Build context
                    context = {
                        "project": memory_dict.get("project"),
                        "language": memory_dict.get("language"),
                        "file_path": memory_dict.get("file_path"),
                        "tags": memory_dict.get("tags", []),
                    }

                    # Extract entities
                    entities = self.ner_service.extract_entities(
                        memory_dict["content"], memory_dict["type"], context
                    )

                    if entities:
                        # Update memory with entities
                        entity_names = [e["name"] for e in entities]
                        conn.execute(
                            "UPDATE memories SET entities = ? WHERE id = ?",
                            (json.dumps(entity_names), memory_dict["id"]),
                        )

                        # Insert/update entities table
                        now = int(datetime.now(UTC).timestamp())

                        for entity in entities:
                            entity_id = f"{entity['type']}:{entity['name']}"

                            # Check if entity exists
                            existing = conn.execute(
                                "SELECT id, mention_count FROM entities WHERE id = ?", (entity_id,)
                            ).fetchone()

                            if existing:
                                # Update
                                conn.execute(
                                    """
                                    UPDATE entities
                                    SET last_seen = ?, mention_count = mention_count + 1
                                    WHERE id = ?
                                    """,
                                    (now, entity_id),
                                )
                            else:
                                # Insert
                                conn.execute(
                                    """
                                    INSERT INTO entities (id, type, name, first_seen, last_seen, mention_count)
                                    VALUES (?, ?, ?, ?, ?, 1)
                                    """,
                                    (entity_id, entity["type"], entity["name"], now, now),
                                )

                            # Link memory to entity
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO memory_entities (memory_id, entity_id, relevance)
                                VALUES (?, ?, ?)
                                """,
                                (memory_dict["id"], entity_id, entity["confidence"]),
                            )

                            # Count entity types
                            entity_counts[entity["type"]] = entity_counts.get(entity["type"], 0) + 1

                        total_entities += len(entities)

                    processed += 1

                except Exception as e:
                    self.logger.error(f"Error extracting entities from {memory['id']}: {e}")
                    errors += 1

            conn.commit()

            self.logger.info(f"Extracted {total_entities} entities")
            if entity_counts:
                self.logger.debug(f"Entity breakdown: {entity_counts}")

            return {
                "processed": processed,
                "skipped": len(memories) - processed - errors,
                "errors": errors,
                "details": {
                    "total_entities": total_entities,
                    "entity_types": entity_counts,
                    "avg_per_memory": total_entities / processed if processed > 0 else 0,
                },
            }

        finally:
            conn.close()


if __name__ == "__main__":
    worker = EntityExtractorWorker()
    result = worker.run()
    print(f"Result: {result}")
