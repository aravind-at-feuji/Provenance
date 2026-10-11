"""
agents/rag/embeddings.py — Embedding service with model dimension safety.

Architecture reference: §K.4 Embedding Model Change Safety.
Stores model name and dimensions alongside vectors to prevent HNSW index corruption.
"""

from __future__ import annotations

from typing import Sequence

import structlog

from app.config import get_settings
from app.modules.ai.provider import BaseAIProvider, get_ai_provider

logger = structlog.get_logger(__name__)


MODEL_DIMENSIONS: dict[str, int] = {
    "voyage-3": 1024,
    "text-embedding-004": 768,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "mock": 1024,
}


class EmbeddingService:
    """
    Vendor-neutral vector embedding generation service.
    """

    def __init__(
        self,
        provider: BaseAIProvider | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self.provider = provider or get_ai_provider()
        self.model = model or settings.embedding_model or "voyage-3"
        self.dimensions = MODEL_DIMENSIONS.get(self.model, settings.embedding_dimensions or 1024)

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate normalized vector embeddings for a batch of texts."""
        if not texts:
            return []

        clean_texts = [t.strip() for t in texts]
        return await self.provider.generate_embeddings(
            clean_texts,
            model=self.model,
            dimensions=self.dimensions,
        )

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        vectors = await self.embed_texts([query])
        return vectors[0] if vectors else []
