import logging
import signal
import sys
import time
from types import FrameType

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import WORKER_SETTINGS
from workers.base_worker import BaseWorker
from workers.importance_scorer import ImportanceScorerWorker

# Registry of available workers
WORKER_REGISTRY: dict[str, type[BaseWorker]] = {
    "importance_scorer": ImportanceScorerWorker,
    # Future workers will be added here
    # 'entity_extractor': EntityExtractorWorker,
    # 'summarizer': SummarizerWorker,
    # 'memory_promoter': MemoryPromoterWorker,
    # 'graph_builder': GraphBuilderWorker
}


class WorkerManager:
    def __init__(self) -> None:
        self.logger = logging.getLogger("WorkerManager")
        self.scheduler = BackgroundScheduler()
        self.workers: dict[str, BaseWorker] = {}
        self.running = False
        self._setup_logging()

    def _setup_logging(self) -> None:
        # Ensure root logger is set up if not already
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def register_worker(self, worker_name: str, worker_cls: type[BaseWorker]) -> None:
        """Manually register a worker class if needed dynamically."""
        WORKER_REGISTRY[worker_name] = worker_cls

    def start(self) -> None:
        """Start the worker manager and all enabled workers."""
        if self.running:
            return

        self.logger.info("Starting Worker Manager...")
        self.running = True

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        # Initialize and schedule enabled workers
        enabled_workers = WORKER_SETTINGS.get("enabled_workers", [])

        for worker_name in enabled_workers:
            if worker_name not in WORKER_REGISTRY:
                self.logger.warning(f"Unknown worker enabled in config: {worker_name}")
                continue

            try:
                # Instantiate worker
                worker_cls = WORKER_REGISTRY[worker_name]
                worker = worker_cls()
                self.workers[worker_name] = worker

                # Get schedule config
                schedule_config = WORKER_SETTINGS.get("schedules", {}).get(worker_name, {})
                interval_minutes = schedule_config.get("interval_minutes", 60)

                # Create trigger (default to interval based)
                trigger = IntervalTrigger(minutes=interval_minutes)

                # Schedule the job
                self.scheduler.add_job(
                    func=worker.run,
                    trigger=trigger,
                    id=worker_name,
                    name=f"Run {worker_name}",
                    replace_existing=True,
                    max_instances=1,
                    coalesce=True,
                )

                self.logger.info(
                    f"Scheduled worker '{worker_name}' to run every {interval_minutes} minutes"
                )

            except Exception as e:
                self.logger.error(f"Failed to initialize worker '{worker_name}': {e}")

        # Start the scheduler
        self.scheduler.start()
        self.logger.info("Worker Manager started successfully")

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop the worker manager and scheduler."""
        if not self.running:
            return

        self.logger.info("Stopping Worker Manager...")
        self.running = False
        self.scheduler.shutdown(wait=True)
        self.logger.info("Worker Manager stopped")

    def _handle_signal(self, signum: int, frame: FrameType | None) -> None:
        """Handle system signals for graceful shutdown."""
        self.logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)


if __name__ == "__main__":
    manager = WorkerManager()
    manager.start()
