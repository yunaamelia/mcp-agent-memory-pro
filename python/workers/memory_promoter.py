"""
Memory Promoter Worker
Promotes memories between tiers (Short → Working → Long)
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from typing import Any

from config import (
    IMPORTANCE_SCORE_THRESHOLD,
    MIN_ACCESS_COUNT_FOR_PROMOTION,
    SHORT_TERM_DAYS,
    WORKING_TERM_DAYS,
)
from workers.base_worker import BaseWorker


class MemoryPromoterWorker(BaseWorker):
    """Worker that promotes memories between tiers"""

    def __init__(self):
        super().__init__("MemoryPromoter")

    def process(self) -> dict[str, Any]:
        """Process memory promotions"""

        conn = self.get_db_connection()

        try:
            promoted_to_working = 0
            promoted_to_long = 0
            archived = 0

            # ================================================================
            # Promotion 1: Short-term → Working
            # ================================================================

            short_term_cutoff = int(
                (datetime.now(UTC) - timedelta(days=SHORT_TERM_DAYS)).timestamp() * 1000
            )

            # Get candidates for working memory
            cursor = conn.execute(
                """
                SELECT id, importance_score, access_count
                FROM memories
                WHERE tier = 'short'
                  AND archived = 0
                  AND timestamp < ?
                  AND (
                      importance_score >= ?
                      OR access_count >= ?
                  )
                """,
                (short_term_cutoff, IMPORTANCE_SCORE_THRESHOLD, MIN_ACCESS_COUNT_FOR_PROMOTION),
            )

            working_candidates = cursor.fetchall()

            for memory in working_candidates:
                conn.execute(
                    "UPDATE memories SET tier = ?  WHERE id = ?", ("working", memory["id"])
                )
                promoted_to_working += 1

                self.logger.debug(
                    f"Promoted to working: {memory['id'][:8]} "
                    f"(importance: {memory['importance_score']:. 2f}, "
                    f"accesses: {memory['access_count']})"
                )

            # ================================================================
            # Promotion 2: Working → Long-term (with summarization flag)
            # ================================================================

            working_term_cutoff = int(
                (datetime.now(UTC) - timedelta(days=WORKING_TERM_DAYS)).timestamp() * 1000
            )

            # Get candidates for long-term memory
            cursor = conn.execute(
                """
                SELECT id, importance_score, access_count
                FROM memories
                WHERE tier = 'working'
                  AND archived = 0
                  AND timestamp < ?
                  AND access_count < ?
                """,
                (working_term_cutoff, MIN_ACCESS_COUNT_FOR_PROMOTION),
            )

            long_candidates = cursor.fetchall()

            # Mark for summarization (will be handled by Summarizer worker)
            for memory in long_candidates:
                conn.execute("UPDATE memories SET tier = ? WHERE id = ?", ("long", memory["id"]))
                promoted_to_long += 1

                self.logger.debug(f"Promoted to long-term: {memory['id'][:8]} (will be summarized)")

            # ================================================================
            # Archival:  Low-value short-term memories
            # ================================================================

            # Archive very old, low-importance, unaccessed short-term memories
            archive_cutoff = int(
                (datetime.now(UTC) - timedelta(days=SHORT_TERM_DAYS * 3)).timestamp() * 1000
            )

            cursor = conn.execute(
                """
                SELECT id
                FROM memories
                WHERE tier = 'short'
                  AND archived = 0
                  AND timestamp < ?
                  AND importance_score < 0.3
                  AND access_count = 0
                """,
                (archive_cutoff,),
            )

            archive_candidates = cursor.fetchall()

            for memory in archive_candidates:
                conn.execute("UPDATE memories SET archived = 1 WHERE id = ?", (memory["id"],))
                archived += 1

            conn.commit()

            self.logger.info(
                f"Promotions:  {promoted_to_working} → working, "
                f"{promoted_to_long} → long-term, "
                f"{archived} archived"
            )

            return {
                "processed": promoted_to_working + promoted_to_long + archived,
                "skipped": 0,
                "errors": 0,
                "details": {
                    "promoted_to_working": promoted_to_working,
                    "promoted_to_long": promoted_to_long,
                    "archived": archived,
                },
            }

        finally:
            conn.close()


if __name__ == "__main__":
    worker = MemoryPromoterWorker()
    result = worker.run()
    print(f"Result:  {result}")
