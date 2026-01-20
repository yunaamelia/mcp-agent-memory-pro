"""
Summarizer Worker
Summarizes long-term memories using Claude API
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import builtins
import contextlib
from typing import Any

from config import CLAUDE_API_KEY, SUMMARIZATION_BATCH_SIZE
from services.claude_client import ClaudeClient
from workers.base_worker import BaseWorker


class SummarizerWorker(BaseWorker):
    """Worker that summarizes memories for long-term storage"""

    def __init__(self):
        super().__init__("Summarizer")

        # Only initialize if API key is available
        if CLAUDE_API_KEY:
            self.claude_client = ClaudeClient()
        else:
            self.claude_client = None
            self.logger.warning("Claude API key not set - summarization disabled")

    def process(self) -> dict[str, Any]:
        """Process memories needing summarization"""

        if not self.claude_client:
            self.logger.info("Summarization skipped - no API key")
            return {"processed": 0, "skipped": 0, "errors": 0, "disabled": True}

        conn = self.get_db_connection()

        try:
            # Get long-term memories without summaries
            cursor = conn.execute(
                """
                SELECT id, type, content, project, language, file_path, tags, entities
                FROM memories
                WHERE tier = 'long'
                  AND archived = 0
                  AND LENGTH(content) > 500
                  AND promoted_from IS NULL
                ORDER BY importance_score DESC
                LIMIT ?
                """,
                (SUMMARIZATION_BATCH_SIZE,),
            )

            memories = cursor.fetchall()

            if not memories:
                self.logger.info("No memories need summarization")
                return {"processed": 0, "skipped": 0, "errors": 0}

            self.logger.info(f"Summarizing {len(memories)} memories...")

            processed = 0
            errors = 0
            total_compression = 0

            for memory in memories:
                try:
                    memory_dict = dict(memory)

                    # Build context
                    context = {
                        "project": memory_dict.get("project"),
                        "language": memory_dict.get("language"),
                        "file_path": memory_dict.get("file_path"),
                    }

                    # Parse tags
                    if memory_dict.get("tags"):
                        with contextlib.suppress(builtins.BaseException):
                            context["tags"] = json.loads(memory_dict["tags"])

                    # Generate summary
                    original_length = len(memory_dict["content"])
                    summary = self.claude_client.summarize_memory(
                        memory_dict["content"], memory_dict["type"], context
                    )
                    summary_length = len(summary)

                    if summary and summary_length < original_length:
                        # Create new summarized memory
                        summarized_id = f"{memory_dict['id']}_summary"
                        now = int(datetime.now(UTC).timestamp() * 1000)

                        # Insert summarized version
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO memories (
                                id, tier, type, source, content, content_hash,
                                timestamp, project, file_path, language, tags, entities,
                                importance_score, access_count, created_at, last_accessed,
                                promoted_from, archived
                            )
                            SELECT
                                ?, tier, type, source, ?, ?,
                                timestamp, project, file_path, language, tags, entities,
                                importance_score, access_count, ?, last_accessed,
                                id, 0
                            FROM memories WHERE id = ?
                            """,
                            (
                                summarized_id,
                                summary,
                                f"summary_{memory_dict['id']}",
                                now,
                                memory_dict["id"],
                            ),
                        )

                        # Archive original
                        conn.execute(
                            "UPDATE memories SET archived = 1 WHERE id = ?", (memory_dict["id"],)
                        )

                        compression_ratio = summary_length / original_length
                        total_compression += compression_ratio

                        self.logger.debug(
                            f"Summarized {memory_dict['id'][:8]}: "
                            f"{original_length}→{summary_length} chars "
                            f"({compression_ratio:.1%} compression)"
                        )

                        processed += 1
                    else:
                        self.logger.warning(f"Summary not shorter for {memory_dict['id'][:8]}")

                except Exception as e:
                    self.logger.error(f"Error summarizing {memory['id']}: {e}")
                    errors += 1

            conn.commit()

            avg_compression = total_compression / processed if processed > 0 else 0

            self.logger.info(
                f"Summarized {processed} memories (avg compression: {avg_compression:. 1%})"
            )

            return {
                "processed": processed,
                "skipped": len(memories) - processed - errors,
                "errors": errors,
                "details": {
                    "avg_compression_ratio": avg_compression,
                    "total_summarized": processed,
                },
            }

        finally:
            conn.close()


if __name__ == "__main__":
    worker = SummarizerWorker()
    result = worker.run()
    print(f"Result: {result}")
