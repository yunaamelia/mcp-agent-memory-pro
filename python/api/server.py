import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add python directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.routes import advanced, analytics, health, query

app = FastAPI(
    title="MCP Agent Memory Pro API",
    description="API for Memory Management, Querying and Analytics",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(advanced.router, prefix="/api/v1", tags=["Advanced"])


@app.get("/")
async def root():
    return {"message": "MCP Agent Memory Pro API"}


if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api.server:app", host=host, port=port, reload=True)
