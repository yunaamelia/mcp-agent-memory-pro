import sqlite3

import config
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


def get_db():
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@router.get("/health")
async def health_check(db: sqlite3.Connection = Depends(get_db)):  # noqa: B008
    try:
        db.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e!s}") from e
