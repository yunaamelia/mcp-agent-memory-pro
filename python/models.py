from pydantic import BaseModel, Field


class EmbedSingleRequest(BaseModel):
    """Request model for single text embedding"""

    text: str = Field(..., min_length=1, description="Text to embed")
    normalize: bool = Field(True, description="Normalize embeddings")


class EmbedBatchRequest(BaseModel):
    """Request model for batch text embedding"""

    texts: list[str] = Field(..., min_items=1, description="List of texts to embed")
    normalize: bool = Field(True, description="Normalize embeddings")


class EmbedSingleResponse(BaseModel):
    """Response model for single embedding"""

    embedding: list[float]
    dimensions: int
    model: str


class EmbedBatchResponse(BaseModel):
    """Response model for batch embeddings"""

    embeddings: list[list[float]]
    dimensions: int
    count: int
    model: str


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    model: str
    dimensions: int
    version: str
