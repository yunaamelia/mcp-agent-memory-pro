"""
Job Scheduler
Schedules and manages background worker jobs
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

sys.path.append(str(Path(__file__).parent.parent))

from config import (
    SCHEDULE_ENTITY_EXTRACTOR,
    SCHEDULE_GRAPH_BUILDER,
    SCHEDULE_IMPORTANCE_SCORER,
    SCHEDULE_MEMORY_PROMOTER,
    SCHEDULE_SUMMARIZER,
)
from workers.entity_extractor import EntityExtractorWorker
from workers.graph_builder import GraphBuilderWorker
from workers.importance_scorer import ImportanceScorerWorker
from workers.memory_promoter import MemoryPromoterWorker
from workers.summarizer import SummarizerWorker


class WorkerScheduler:
    """Scheduler for background workers"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.logger = logging.getLogger("WorkerScheduler")
        self.workers = {}
        self.last_results = {}

    def initialize_workers(self):
        """Initialize all workers"""

        self.workers = {
            "importance_scorer": ImportanceScorerWorker(),
            "entity_extractor": EntityExtractorWorker(),
            "memory_promoter": MemoryPromoterWorker(),
            "summarizer": SummarizerWorker(),
            "graph_builder": GraphBuilderWorker(),
        }

        self.logger.info(f"Initialized {len(self.workers)} workers")

    def schedule_jobs(self):
        """Schedule all worker jobs"""

        # Importance Scorer - Every 5 minutes
        self.scheduler.add_job(
            func=self._run_worker,
            args=["importance_scorer"],
            trigger=CronTrigger.from_crontab(SCHEDULE_IMPORTANCE_SCORER),
            id="importance_scorer",
            name="Importance Scorer",
            replace_existing=True,
        )

        # Entity Extractor - Every 15 minutes
        self.scheduler.add_job(
            func=self._run_worker,
            args=["entity_extractor"],
            trigger=CronTrigger.from_crontab(SCHEDULE_ENTITY_EXTRACTOR),
            id="entity_extractor",
            name="Entity Extractor",
            replace_existing=True,
        )

        # Memory Promoter - Hourly
        self.scheduler.add_job(
            func=self._run_worker,
            args=["memory_promoter"],
            trigger=CronTrigger.from_crontab(SCHEDULE_MEMORY_PROMOTER),
            id="memory_promoter",
            name="Memory Promoter",
            replace_existing=True,
        )

        # Summarizer - Daily at 2 AM
        self.scheduler.add_job(
            func=self._run_worker,
            args=["summarizer"],
            trigger=CronTrigger.from_crontab(SCHEDULE_SUMMARIZER),
            id="summarizer",
            name="Summarizer",
            replace_existing=True,
        )

        # Graph Builder - Daily at 3 AM
        self.scheduler.add_job(
            func=self._run_worker,
            args=["graph_builder"],
            trigger=CronTrigger.from_crontab(SCHEDULE_GRAPH_BUILDER),
            id="graph_builder",
            name="Graph Builder",
            replace_existing=True,
        )

        self.logger.info("Scheduled all jobs")

    def _run_worker(self, worker_name: str):
        """Run a specific worker"""

        worker = self.workers.get(worker_name)
        if not worker:
            self.logger.error(f"Worker not found: {worker_name}")
            return

        self.logger.info(f"Running worker: {worker_name}")

        result = worker.run()
        self.last_results[worker_name] = {"timestamp": datetime.now().isoformat(), "result": result}

        if result["success"]:
            self.logger.info(f"Worker {worker_name} completed successfully")
        else:
            self.logger.error(f"Worker {worker_name} failed: {result.get('error')}")

    def start(self):
        """Start the scheduler"""

        self.initialize_workers()
        self.schedule_jobs()
        self.scheduler.start()

        self.logger.info("Worker scheduler started")

    def stop(self):
        """Stop the scheduler"""

        self.scheduler.shutdown()
        self.logger.info("Worker scheduler stopped")

    def get_status(self) -> dict[str, Any]:
        """Get scheduler status"""

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                }
            )

        return {
            "running": self.scheduler.running,
            "jobs": jobs,
            "last_results": self.last_results,
            "worker_metrics": {name: worker.get_metrics() for name, worker in self.workers.items()},
        }

    def run_worker_now(self, worker_name: str) -> dict[str, Any]:
        """Manually trigger a worker"""

        if worker_name not in self.workers:
            return {"error": f"Worker not found: {worker_name}"}

        self._run_worker(worker_name)
        return self.last_results.get(worker_name, {})
