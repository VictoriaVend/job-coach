"""Embedding service: generate and manage text embeddings."""

from __future__ import annotations

from job_coach.app.core.config import settings


class EmbeddingService:
    """Generates text embeddings using sentence-transformers.

    The model is loaded lazily on first use to avoid startup overhead.
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_ID
        self._model = None

    @property
    def model(self):
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required. "
                    "Install: pip install sentence-transformers"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        return self.model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        return self.model.encode(texts).tolist()

    @property
    def dimension(self) -> int:
        """Return the dimensionality of embeddings for this model."""
        return self.model.get_sentence_embedding_dimension()


# Module-level singleton (lazy)
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Return a singleton EmbeddingService instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
