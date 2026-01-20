"""
Base Worker Class
All background workers inherit from this base class
"""

import logging
import sqlite3
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent.parent))

from config import DB_PATH, WORKER_LOG_DIR


class BaseWorker(ABC):
    """Base class for all background workers"""

    def __init__(self, name: str, log_level: str = "INFO"):
        self.name = name
        self.logger = self._setup_logger(log_level)
        self.db_path = DB_PATH
        self.metrics: dict[str, Any] = {
            "runs": 0,
            "successes": 0,
            "failures": 0,
            "total_duration": 0.0,
            "last_run": None,
            "last_error": None,
        }

    def _setup_logger(self, log_level: str) -> logging.Logger:
        """Setup worker-specific logger"""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, log_level))

        # File handler
        log_file = WORKER_LOG_DIR / f"{self.name}.log"
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @abstractmethod
    def process(self) -> dict[str, Any]:
        """
        Main worker logic - must be implemented by subclasses

        Returns:
            Dict with processing results:
            {
                'processed': int,
                'skipped': int,
                'errors': int,
                'details': Any
            }
        """
        pass

    def run(self) -> dict[str, Any]:
        """
        Execute worker with error handling and metrics

        Returns:
            Dict with execution results
        """
        start_time = time.time()
        self.metrics["runs"] += 1
        self.metrics["last_run"] = datetime.utcnow().isoformat()

        self.logger.info(f"Starting {self.name}...")

        try:
            result = self.process()

            duration = time.time() - start_time
            self.metrics["successes"] += 1
            self.metrics["total_duration"] += duration

            self.logger.info(
                f"{self.name} completed in {duration:.2f}s - "
                f"Processed: {result.get('processed', 0)}, "
                f"Errors: {result.get('errors', 0)}"
            )

            return {
                "success": True,
                "duration": duration,
                "metrics": self.metrics,
                "result": result,
            }

        except Exception as e:
            duration = time.time() - start_time
            self.metrics["failures"] += 1
            self.metrics["last_error"] = str(e)

            self.logger.error(f"{self.name} failed: {e}", exc_info=True)

            return {
                "success": False,
                "duration": duration,
                "error": str(e),
                "metrics": self.metrics,
            }

    def get_metrics(self) -> dict[str, Any]:
        """Get worker metrics"""
        avg_duration = (
            self.metrics["total_duration"] / self.metrics["runs"] if self.metrics["runs"] > 0 else 0
        )

        return {
            **self.metrics,
            "avg_duration": avg_duration,
            "success_rate": (
                self.metrics["successes"] / self.metrics["runs"] if self.metrics["runs"] > 0 else 0
            ),
        }
