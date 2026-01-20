#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from worker_manager import WorkerManager  # noqa: E402


def main() -> None:
    """Main entry point for running background workers."""
    # Ensure logs directory exists
    log_dir = current_dir.parent / "logs" / "workers"
    log_dir.mkdir(parents=True, exist_ok=True)

    try:
        manager = WorkerManager()
        manager.start()
    except Exception as e:
        logging.error(f"Fatal error in worker wrapper: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
