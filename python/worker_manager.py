#!/usr/bin/env python3
"""
Worker Manager
Main entry point for background workers
"""

import logging
import signal
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from config import WORKER_LOG_DIR, WORKERS_ENABLED
from jobs.scheduler import WorkerScheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(WORKER_LOG_DIR / "worker_manager.log"), logging.StreamHandler()],
)

logger = logging.getLogger("WorkerManager")

# Global scheduler instance
scheduler = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    if scheduler:
        scheduler.stop()
    sys.exit(0)


def main():
    """Main entry point"""

    global scheduler

    if not WORKERS_ENABLED:
        logger.warning("Workers disabled in configuration")
        return

    logger.info("=" * 60)
    logger.info("MCP Agent Memory Pro - Worker Manager")
    logger.info("=" * 60)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start scheduler
    scheduler = WorkerScheduler()
    scheduler.start()

    logger.info("Worker manager running.  Press Ctrl+C to stop.")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        scheduler.stop()


if __name__ == "__main__":
    main()
