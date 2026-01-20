"""
Importance Scorer Worker
Recalculates importance scores for memories
"""

import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent.parent))

from config import BATCH_SIZE
from services.scoring_service import ImportanceScoringService
from workers.base_worker import BaseWorker


class ImportanceScorerWorker(BaseWorker):
    """Worker that recalculates importance scores"""

    def __init__(self):
        super().__init__("ImportanceScorer")

    def process(self) -> dict[str, Any]:
        """Process memories needing importance scoring"""

        conn = self.get_db_connection()
        scorer = ImportanceScoringService(conn)

        try:
            # Check if importance_score column exists, if not, print warning (handling implicit schema issues)
            # In a real migration scenario, we would add the column.
            # For now assuming schema is handled or will be handled.

            # Get memories that need scoring (new or low confidence)
            # We select where importance_score is NULL or it's been a while (optional logic for re-scoring)
            # Using a simplified query to target NULLs first
            cursor = conn.execute(
                """
                SELECT id, type, source, content, timestamp, access_count,
                       created_at, project, file_path, tags, importance_score
                FROM memories
                WHERE archived = 0
                  AND (
                      importance_score IS NULL
                  )
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (BATCH_SIZE,),
            )

            memories = cursor.fetchall()

            if not memories:
                # If no NULLs, look for things to update periodically?
                # For now just return, as we want to fill backfill first
                self.logger.info("No un-scored memories found.")
                return {"processed": 0, "skipped": 0, "errors": 0}

            self.logger.info(f"Scoring {len(memories)} memories...")

            processed = 0
            errors = 0
            score_changes = []

            for memory in memories:
                try:
                    memory_dict = dict(memory)

                    # Parse tags
                    if memory_dict.get("tags") and isinstance(memory_dict["tags"], str):
                        try:
                            memory_dict["tags"] = json.loads(memory_dict["tags"])
                        except:
                            memory_dict["tags"] = []

                    # Calculate new importance
                    new_score = scorer.calculate_importance(memory_dict)
                    old_score = (
                        memory_dict["importance_score"]
                        if memory_dict["importance_score"] is not None
                        else 0.5
                    )

                    # Update
                    conn.execute(
                        "UPDATE memories SET importance_score = ? WHERE id = ?",
                        (new_score, memory_dict["id"]),
                    )

                    if abs(new_score - old_score) > 0.05:
                        score_changes.append(
                            {
                                "id": memory_dict["id"],
                                "old": old_score,
                                "new": new_score,
                                "delta": new_score - old_score,
                            }
                        )

                    processed += 1

                except Exception as e:
                    self.logger.error(f"Error scoring memory {memory['id']}: {e}")
                    errors += 1

            conn.commit()

            # Log significant changes
            if score_changes:
                self.logger.info(f"Updated {len(score_changes)} scores")
                for change in sorted(score_changes, key=lambda x: abs(x["delta"]), reverse=True)[
                    :5
                ]:
                    self.logger.debug(
                        f"  {change['id'][:8]}: {change['old']:.2f} -> {change['new']:.2f} "
                        f"({change['delta']:+.2f})"
                    )

            return {
                "processed": processed,
                "skipped": len(memories) - processed - errors,
                "errors": errors,
                "details": {
                    "score_changes": len(score_changes),
                    "avg_score": sum(c["new"] for c in score_changes) / len(score_changes)
                    if score_changes
                    else 0,
                },
            }

        finally:
            conn.close()


if __name__ == "__main__":
    worker = ImportanceScorerWorker()
    result = worker.run()
    # Print result to stdout for manual verification
    print(json.dumps(result, indent=2, default=str))
