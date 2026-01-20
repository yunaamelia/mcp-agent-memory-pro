"""
FastAPI Embedding Service
Provides embedding generation using Sentence Transformers
"""

import logging
import time
from contextlib import asynccontextmanager

from config import CACHE_DIR, MAX_BATCH_SIZE, MODEL_NAME
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from models import (
    EmbedBatchRequest,
    EmbedBatchResponse,
    EmbedSingleRequest,
    EmbedSingleResponse,
    HealthResponse,
)
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Global model variable
model: SentenceTransformer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for model loading"""
    global model

    logger.info(f"Loading embedding model: {MODEL_NAME}")
    start_time = time.time()

    try:
        model = SentenceTransformer(MODEL_NAME, cache_folder=str(CACHE_DIR))
        load_time = time.time() - start_time
        logger.info(f"Model loaded successfully in {load_time:.2f}s")
        logger.info(f"Embedding dimensions: {model.get_sentence_embedding_dimension()}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down embedding service")


# Create FastAPI app
app = FastAPI(
    title="MCP Agent Memory - Embedding Service",
    description="Embedding generation service using Sentence Transformers",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": "MCP Agent Memory - Embedding Service",
        "version": "1.0.0",
        "model": MODEL_NAME,
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded"
        )

    return HealthResponse(
        status="healthy",
        model=MODEL_NAME,
        dimensions=model.get_sentence_embedding_dimension(),
        version="1.0.0",
    )


@app.post("/embed/single", response_model=EmbedSingleResponse)
async def embed_single(request: EmbedSingleRequest):
    """
    Generate embedding for a single text

    Args:
        request: Single embedding request

    Returns:
        EmbedSingleResponse with embedding vector
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded"
        )

    try:
        logger.debug(f"Generating embedding for text (length: {len(request.text)})")

        embedding = model.encode(
            request.text, normalize_embeddings=request.normalize, show_progress_bar=False
        )

        return EmbedSingleResponse(
            embedding=embedding.tolist(), dimensions=len(embedding), model=MODEL_NAME
        )

    except Exception as e:
        logger.error(f"Error generating embedding: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {e!s}",
        )


@app.post("/embed/batch", response_model=EmbedBatchResponse)
async def embed_batch(request: EmbedBatchRequest):
    """
    Generate embeddings for multiple texts

    Args:
        request:  Batch embedding request

    Returns:
        EmbedBatchResponse with embedding vectors
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded"
        )

    if len(request.texts) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size exceeds maximum of {MAX_BATCH_SIZE}",
        )

    try:
        logger.info(f"Generating embeddings for {len(request.texts)} texts")

        embeddings = model.encode(
            request.texts,
            normalize_embeddings=request.normalize,
            show_progress_bar=False,
            batch_size=min(len(request.texts), 32),
        )

        return EmbedBatchResponse(
            embeddings=embeddings.tolist(),
            dimensions=len(embeddings[0]),
            count=len(embeddings),
            model=MODEL_NAME,
        )

    except Exception as e:
        logger.error(f"Error generating embeddings: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch embedding generation failed: {e!s}",
        )


@app.get("/stats", response_model=dict)
async def stats():
    """Get service statistics"""
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded"
        )

    return {
        "model": MODEL_NAME,
        "dimensions": model.get_sentence_embedding_dimension(),
        "max_batch_size": MAX_BATCH_SIZE,
        "cache_dir": str(CACHE_DIR),
    }


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT, WORKERS

    uvicorn.run("embedding_service:app", host=HOST, port=PORT, workers=WORKERS, log_level="info")
