"""
REST API
External API for integrations
"""

import os
import sqlite3

# Import services
import sys
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent.parent))

from analytics.dashboard_service import DashboardService
from data_management.export_service import ExportService
from monitoring.health_monitor import HealthMonitor

# Constants
DB_PATH = os.getenv('MCP_MEMORY_DB_PATH', 'data/memories.db')
DATA_DIR = os.getenv('MCP_MEMORY_DATA_DIR', 'data')

# API Models
class MemoryQuery(BaseModel):
    query: str
    limit: int | None = 10


class ExportRequest(BaseModel):
    format: str = 'json'  # json, csv
    filters: dict | None = None


class HealthResponse(BaseModel):
    status: str
    database:  dict
    storage: dict


# Create FastAPI app
app = FastAPI(
    title="MCP Agent Memory Pro API",
    description="REST API for MCP Agent Memory Pro",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency:  Get DB connection
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Authentication (simple API key)
async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key"""

    # For now, accept any key or no key
    # In production, validate against configured keys
    return True


# Routes

@app.get("/")
async def root():
    """API root"""
    return {
        "service": "MCP Agent Memory Pro API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analytics": "/analytics/overview",
            "memories": "/memories",
            "export": "/export"
        }
    }


@app.get("/health")
async def health(conn: sqlite3.Connection = Depends(get_db)):
    """Health check endpoint"""

    monitor = HealthMonitor(conn, Path(DATA_DIR))
    health_status = monitor.get_health_status()

    return health_status


@app.get("/analytics/overview")
async def analytics_overview(
    conn: sqlite3.Connection = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Get analytics overview"""

    service = DashboardService(conn)
    try:
        overview = service.get_overview()
    except Exception:
        # Fallback if analytics tables aren't populated yet
        overview = {"status": "Metrics collecting..."}

    return overview


@app.get("/analytics/timeline")
async def analytics_timeline(
    days: int = 30,
    conn: sqlite3.Connection = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Get activity timeline"""

    service = DashboardService(conn)
    timeline = service.get_activity_timeline(days)

    return {
        "days": days,
        "timeline":  timeline
    }


@app. get("/analytics/projects")
async def analytics_projects(
    conn: sqlite3.Connection = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Get project breakdown"""

    service = DashboardService(conn)
    projects = service.get_project_breakdown()

    return {
        "projects": projects,
        "count": len(projects)
    }


@app.get("/memories")
async def list_memories(
    limit: int = 10,
    type: str | None = None,
    project: str | None = None,
    conn: sqlite3.Connection = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """List memories with filters"""

    query = "SELECT * FROM memories WHERE archived = 0"
    params = []

    if type:
        query += " AND type = ?"
        params.append(type)

    if project:
        query += " AND project = ?"
        params. append(project)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    cursor = conn.execute(query, params)
    memories = [dict(row) for row in cursor.fetchall()]

    return {
        "memories": memories,
        "count": len(memories)
    }


@app.get("/memories/{memory_id}")
async def get_memory(
    memory_id:  str,
    conn: sqlite3.Connection = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Get specific memory"""

    cursor = conn.execute('SELECT * FROM memories WHERE id = ? ', (memory_id,))
    memory = cursor.fetchone()

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    return dict(memory)


@app.post("/export")
async def export_data(
    request: ExportRequest,
    conn: sqlite3.Connection = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Export data"""

    service = ExportService(conn)

    output_path = Path(DATA_DIR) / 'exports' / f'export_{int(time.time())}.{request.format}'

    if request.format == 'json':
        result = service.export_to_json(str(output_path), request.filters)
    elif request.format == 'csv':
        result = service.export_to_csv(str(output_path), request.filters)
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

    return result


@app.get("/stats")
async def get_stats(
    conn: sqlite3.Connection = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Get statistics"""

    service = DashboardService(conn)

    # Try getting health metrics if method exists, else mock/skip for now
    monitor = HealthMonitor(conn, Path(DATA_DIR))
    health = monitor.get_health_status()

    return {
        "overview": service.get_overview(),
        "usage": service.get_usage_stats(),
        "health": health
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
