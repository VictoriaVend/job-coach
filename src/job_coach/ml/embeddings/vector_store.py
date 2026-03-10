"""Qdrant vector store client for storing and retrieving embeddings."""

from __future__ import annotations

from job_coach.app.core.config import settings


class VectorStore:
    """Client for Qdrant vector database operations.

    Manages collections, upsert, and similarity search.
    """

    COLLECTION_NAME = "documents"

    def __init__(self, url: str | None = None):
        self.url = url or settings.QDRANT_URL
        self._client = None

    @property
    def client(self):
        """Lazy-load the Qdrant client."""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
            except ImportError as exc:
                raise ImportError(
                    "qdrant-client is required. Install: pip install qdrant-client"
                ) from exc
            self._client = QdrantClient(url=self.url)
        return self._client

    def ensure_collection(self, vector_size: int) -> None:
        """Create the collection if it doesn't exist."""
        from qdrant_client.models import Distance, VectorParams

        collections = [c.name for c in self.client.get_collections().collections]
        if self.COLLECTION_NAME not in collections:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def upsert_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]],
        user_id: int,
        document_id: int,
        document_type: str = "resume",
    ) -> None:
        """Store document chunks with their embeddings in Qdrant.

        Args:
            chunks: List of chunk dicts from ingestion.parser.chunk_text().
            embeddings: Corresponding embedding vectors.
            user_id: Owner user ID for filtering.
            document_id: Source document ID (resume_id / job_id).
            document_type: 'resume' or 'job_description'.
        """
        from qdrant_client.models import PointStruct

        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = hash(f"{document_type}_{document_id}_{chunk['chunk_index']}") % (
                2**63
            )
            points.append(
                PointStruct(
                    id=abs(point_id),
                    vector=embedding,
                    payload={
                        "text": chunk["text"],
                        "chunk_index": chunk["chunk_index"],
                        "user_id": user_id,
                        "document_id": document_id,
                        "document_type": document_type,
                    },
                )
            )

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points,
        )

    def search(
        self,
        query_embedding: list[float],
        user_id: int,
        top_k: int = 5,
    ) -> list[dict]:
        """Search for similar documents, filtered by user.

        Args:
            query_embedding: Query vector.
            user_id: Only return results belonging to this user.
            top_k: Number of results to return.

        Returns:
            List of dicts with 'text', 'score', 'document_id', 'document_type'.
        """
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id),
                    )
                ]
            ),
            limit=top_k,
        )

        return [
            {
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "document_id": hit.payload.get("document_id"),
                "document_type": hit.payload.get("document_type"),
                "chunk_index": hit.payload.get("chunk_index"),
            }
            for hit in results.points
        ]


# Module-level singleton
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Return a singleton VectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
