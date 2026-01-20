import sqlite3

import config
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from query.memql_executor import MemQLExecutor

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


def get_db():
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@router.post("/query/execute")
async def execute_query(request: QueryRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        executor = MemQLExecutor(db)
        result = executor.execute(request.query)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
