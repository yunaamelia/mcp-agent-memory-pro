"""
Memory Consolidator Worker
Periodically consolidates, deduplicates, and cleans up memories
"""

import sys
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from workers.base_worker import BaseWorker


class MemoryConsolidatorWorker(BaseWorker):
    """Worker that consolidates and cleans up memories"""

    def __init__(self):
        super().__init__("MemoryConsolidator")
        self.consolidation_service = None
        self.clustering_service = None

    def _get_services(self):
        """Lazy load cognitive services"""
        if self.consolidation_service is None:
            try:
                from cognitive.clustering_service import get_clustering_service
                from cognitive.consolidation_service import get_consolidation_service

                db_path = str(Path(__file__).parent.parent.parent / "data" / "memory.db")
                self.consolidation_service = get_consolidation_service(db_path)
                self.clustering_service = get_clustering_service(db_path)
            except ImportError as e:
                self.logger.error(f"Failed to import cognitive services: {e}")
                raise

    def process(self) -> dict[str, Any]:
        """Run consolidation process"""

        self._get_services()

        results = {
            "duplicates_found": 0,
            "duplicates_merged": 0,
            "garbage_collected": 0,
            "clusters_identified": 0,
            "errors": [],
        }

        # Step 1: Find and merge exact duplicates
        try:
            duplicates = self.consolidation_service.find_duplicates(
                similarity_threshold=0.95  # High threshold for auto-merge
            )

            results["duplicates_found"] = len(duplicates)

            # Auto-merge exact duplicates only
            for dup in duplicates:
                if dup.get("type") == "exact_duplicate" and dup.get("count", 0) > 1:
                    try:
                        merge_result = self.consolidation_service.merge_memories(
                            dup["memory_ids"], strategy="keep_best"
                        )
                        if "error" not in merge_result:
                            results["duplicates_merged"] += merge_result.get("archived_count", 0)
                    except Exception as e:
                        results["errors"].append(f"Merge error: {e!s}")

            self.logger.info(f"Merged {results['duplicates_merged']} duplicate memories")

        except Exception as e:
            results["errors"].append(f"Duplicate detection error: {e!s}")
            self.logger.error(f"Duplicate detection failed: {e}")

        # Step 2: Garbage collect low-value memories
        try:
            gc_result = self.consolidation_service.garbage_collect(
                max_age_days=90,
                min_importance=0.2,
                dry_run=False,  # Actually archive
            )

            results["garbage_collected"] = gc_result.get("archived", 0)
            self.logger.info(f"Garbage collected {results['garbage_collected']} memories")

        except Exception as e:
            results["errors"].append(f"Garbage collection error: {e!s}")
            self.logger.error(f"Garbage collection failed: {e}")

        # Step 3: Identify clusters for potential consolidation
        try:
            cluster_result = self.clustering_service.cluster_memories(min_cluster_size=5)

            if "num_clusters" in cluster_result:
                results["clusters_identified"] = cluster_result["num_clusters"]

                # Log large clusters that might benefit from abstraction
                for cluster in cluster_result.get("clusters", []):
                    if cluster.get("size", 0) >= 10:
                        self.logger.info(f"Large cluster found: {cluster.get('size')} memories")

        except Exception as e:
            results["errors"].append(f"Clustering error: {e!s}")
            self.logger.warning(f"Clustering failed (optional): {e}")

        return {
            "processed": results["duplicates_merged"] + results["garbage_collected"],
            "skipped": 0,
            "errors": len(results["errors"]),
            "details": results,
        }


if __name__ == "__main__":
    worker = MemoryConsolidatorWorker()
    result = worker.run()
    print(f"Result: {result}")
