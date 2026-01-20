#!/usr/bin/env python3
"""
Test Job Scheduler
Tests APScheduler integration and job management
"""

import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))


def test_scheduler_initialization():
    """Test scheduler can be initialized"""

    print("Testing Scheduler Initialization")
    print("-" * 40)

    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BackgroundScheduler()

    # Add a test job
    def test_job():
        pass

    scheduler.add_job(
        func=test_job,
        trigger=CronTrigger.from_crontab("*/5 * * * *"),
        id="test_job",
        name="Test Job",
    )

    jobs = scheduler.get_jobs()
    assert len(jobs) == 1, "Job not added"
    assert jobs[0].id == "test_job", "Wrong job ID"

    print(f"  Added job: {jobs[0].name}")
    print("  ✅ Scheduler initialization test passed\n")


def test_cron_triggers():
    """Test cron trigger parsing"""

    print("Testing Cron Triggers")
    print("-" * 40)

    from apscheduler.triggers.cron import CronTrigger

    cron_tests = [
        ("*/5 * * * *", "Every 5 minutes"),
        ("*/15 * * * *", "Every 15 minutes"),
        ("0 * * * *", "Hourly"),
        ("0 2 * * *", "Daily at 2 AM"),
        ("0 3 * * *", "Daily at 3 AM"),
    ]

    for cron_expr, description in cron_tests:
        try:
            trigger = CronTrigger.from_crontab(cron_expr)
            next_fire = trigger.get_next_fire_time(None, datetime.now())
            print(f"  {description}: {cron_expr} → Next: {next_fire}")
        except Exception as e:
            print(f"  ❌ Failed to parse {cron_expr}: {e}")
            raise

    print("  ✅ Cron trigger test passed\n")


def test_config_schedules():
    """Test configuration schedule values"""

    print("Testing Config Schedules")
    print("-" * 40)

    from apscheduler.triggers.cron import CronTrigger
    from config import (
        SCHEDULE_ENTITY_EXTRACTOR,
        SCHEDULE_GRAPH_BUILDER,
        SCHEDULE_IMPORTANCE_SCORER,
        SCHEDULE_MEMORY_PROMOTER,
        SCHEDULE_SUMMARIZER,
    )

    schedules = {
        "Importance Scorer": SCHEDULE_IMPORTANCE_SCORER,
        "Entity Extractor": SCHEDULE_ENTITY_EXTRACTOR,
        "Memory Promoter": SCHEDULE_MEMORY_PROMOTER,
        "Summarizer": SCHEDULE_SUMMARIZER,
        "Graph Builder": SCHEDULE_GRAPH_BUILDER,
    }

    for name, schedule in schedules.items():
        try:
            CronTrigger.from_crontab(schedule)
            print(f"  {name}: {schedule} ✓")
        except Exception:
            print(f"  ❌ Invalid schedule for {name}: {schedule}")
            raise

    print("  ✅ Config schedules test passed\n")


def test_worker_scheduler_class():
    """Test WorkerScheduler class"""

    print("Testing WorkerScheduler Class")
    print("-" * 40)

    from jobs.scheduler import WorkerScheduler

    scheduler = WorkerScheduler()

    # Test initialization
    assert scheduler.scheduler is not None, "Scheduler not created"
    assert scheduler.workers == {}, "Workers should be empty before init"

    # Initialize workers
    scheduler.initialize_workers()

    assert len(scheduler.workers) == 5, f"Expected 5 workers, got {len(scheduler.workers)}"

    worker_names = list(scheduler.workers.keys())
    expected = [
        "importance_scorer",
        "entity_extractor",
        "memory_promoter",
        "summarizer",
        "graph_builder",
    ]

    for expected_name in expected:
        assert expected_name in worker_names, f"Missing worker: {expected_name}"
        print(f"  {expected_name}: initialized ✓")

    print("  ✅ WorkerScheduler class test passed\n")


def test_scheduler_lifecycle():
    """Test scheduler start/stop lifecycle"""

    print("Testing Scheduler Lifecycle")
    print("-" * 40)

    from jobs.scheduler import WorkerScheduler

    scheduler = WorkerScheduler()
    scheduler.initialize_workers()
    scheduler.schedule_jobs()

    # Start scheduler
    scheduler.scheduler.start()

    assert scheduler.scheduler.running, "Scheduler not running"
    print("  ✓ Scheduler started")

    # Let it run briefly
    time.sleep(1)

    # Get jobs
    jobs = scheduler.scheduler.get_jobs()
    print(f"  ✓ Active jobs: {len(jobs)}")
    assert len(jobs) == 5, f"Expected 5 jobs, got {len(jobs)}"

    # Stop scheduler
    scheduler.scheduler.shutdown(wait=False)

    print("  ✓ Scheduler stopped")
    print("  ✅ Scheduler lifecycle test passed\n")


def test_get_status():
    """Test scheduler status retrieval"""

    print("Testing Scheduler Status")
    print("-" * 40)

    from jobs.scheduler import WorkerScheduler

    scheduler = WorkerScheduler()
    scheduler.initialize_workers()
    scheduler.schedule_jobs()

    status = scheduler.get_status()

    assert "running" in status, "No running status"
    assert "workers" in status, "No workers in status"
    assert "jobs" in status, "No jobs in status"

    print(f"  Running: {status['running']}")
    print(f"  Workers: {len(status['workers'])}")
    print(f"  Jobs: {len(status['jobs'])}")

    print("  ✅ Scheduler status test passed\n")


def main():
    """Run all scheduler tests"""

    print("\n" + "=" * 50)
    print("JOB SCHEDULER VALIDATION")
    print("=" * 50 + "\n")

    try:
        test_scheduler_initialization()
        test_cron_triggers()
        test_config_schedules()
        test_worker_scheduler_class()
        test_scheduler_lifecycle()
        test_get_status()

        print("=" * 50)
        print("✅ ALL SCHEDULER TESTS PASSED")
        print("=" * 50)

        return 0

    except Exception as e:
        print(f"\n❌ Scheduler tests failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
