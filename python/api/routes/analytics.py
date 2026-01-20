import sqlite3

import config
from analytics.dashboard_service import DashboardService
from fastapi import APIRouter, Depends

router = APIRouter()


def get_db():
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@router.get("/analytics/overview")
async def get_overview(db: sqlite3.Connection = Depends(get_db)):  # noqa: B008
    service = DashboardService(db)
    return service.get_overview()


@router.get("/analytics/timeline")
async def get_timeline(days: int = 30, db: sqlite3.Connection = Depends(get_db)):  # noqa: B008
    service = DashboardService(db)
    return service.get_activity_timeline(days)


@router.get("/analytics/projects")
async def get_projects(db: sqlite3.Connection = Depends(get_db)):  # noqa: B008
    service = DashboardService(db)
    return service.get_project_breakdown()


@router.get("/analytics/usage")
async def get_usage(db: sqlite3.Connection = Depends(get_db)):  # noqa: B008
    service = DashboardService(db)
    return service.get_usage_stats()


@router.get("/analytics/health")
async def get_health_metrics(db: sqlite3.Connection = Depends(get_db)):  # noqa: B008
    service = DashboardService(db)
    return service.get_health_metrics()
