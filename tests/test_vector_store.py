"""Tests for VectorStore Qdrant client."""

from unittest.mock import MagicMock, patch

import pytest
from job_coach.ml.embeddings.vector_store import VectorStore, get_vector_store


class TestVectorStore:
    @patch("job_coach.ml.embeddings.vector_store.QdrantClient")
    def test_init_with_url(self, mock_qdrant_client):
        url = "http://localhost:6333"
        store = VectorStore(url=url)
        assert store.url == url
        assert store._client is None

    @patch("job_coach.ml.embeddings.vector_store.QdrantClient")
    def test_client_property_lazy_load(self, mock_qdrant_client):
        mock_client_instance = MagicMock()
        mock_qdrant_client.return_value = mock_client_instance

        store = VectorStore()
        client = store.client
        assert client is mock_client_instance
        mock_qdrant_client.assert_called_once_with(url=store.url)

        # Second access should return cached client
        client2 = store.client
        assert client2 is mock_client_instance
        assert mock_qdrant_client.call_count == 1

    @patch("job_coach.ml.embeddings.vector_store.QdrantClient")
    def test_client_import_error(self, mock_qdrant_client):
        mock_qdrant_client.side_effect = ImportError("No module named 'qdrant_client'")
        store = VectorStore()
        with pytest.raises(ImportError, match="qdrant-client is required"):
            _ = store.client

    @patch("job_coach.ml.embeddings.vector_store.QdrantClient")
    def test_ensure_collection_creates_if_not_exists(self, mock_qdrant_client):
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = MagicMock(collections=[])

        store = VectorStore()
        store.ensure_collection(vector_size=384)

        mock_client.get_collections.assert_called_once()
        mock_client.create_collection.assert_called_once()
        args, kwargs = mock_client.create_collection.call_args
        assert kwargs["collection_name"] == "documents"
        assert kwargs["vectors_config"].size == 384

    @patch("job_coach.ml.embeddings.vector_store.QdrantClient")
    def test_ensure_collection_skips_if_exists(self, mock_qdrant_client):
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = MagicMock(
            collections=[MagicMock(name="documents")]
        )

        store = VectorStore()
        store.ensure_collection(vector_size=384)

        mock_client.get_collections.assert_called_once()
        mock_client.create_collection.assert_not_called()

    @patch("job_coach.ml.embeddings.vector_store.QdrantClient")
    def test_upsert_chunks(self, mock_qdrant_client):
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client

        store = VectorStore()
        chunks = [
            {"text": "chunk1", "chunk_index": 0},
            {"text": "chunk2", "chunk_index": 1},
        ]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        user_id = 1
        document_id = 10
        document_type = "resume"

        store.upsert_chunks(chunks, embeddings, user_id, document_id, document_type)

        mock_client.upsert.assert_called_once()
        args, kwargs = mock_client.upsert.call_args
        assert kwargs["collection_name"] == "documents"
        points = kwargs["points"]
        assert len(points) == 2
        assert points[0].vector == [0.1, 0.2]
        assert points[0].payload["text"] == "chunk1"
        assert points[0].payload["user_id"] == 1
        assert points[0].payload["document_id"] == 10
        assert points[0].payload["document_type"] == "resume"

    @patch("job_coach.ml.embeddings.vector_store.QdrantClient")
    def test_search(self, mock_qdrant_client):
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client

        # Mock query_points result
        mock_hit1 = MagicMock()
        mock_hit1.payload = {
            "text": "result1",
            "document_id": 1,
            "document_type": "resume",
            "chunk_index": 0,
        }
        mock_hit1.score = 0.9
        mock_hit2 = MagicMock()
        mock_hit2.payload = {
            "text": "result2",
            "document_id": 2,
            "document_type": "job",
            "chunk_index": 1,
        }
        mock_hit2.score = 0.8
        mock_client.query_points.return_value = MagicMock(points=[mock_hit1, mock_hit2])

        store = VectorStore()
        results = store.search(query_embedding=[0.5, 0.6], user_id=1, top_k=5)

        mock_client.query_points.assert_called_once()
        args, kwargs = mock_client.query_points.call_args
        assert kwargs["collection_name"] == "documents"
        assert kwargs["query"] == [0.5, 0.6]
        assert kwargs["limit"] == 5
        assert kwargs["query_filter"].must[0].key == "user_id"

        assert len(results) == 2
        assert results[0]["text"] == "result1"
        assert results[0]["score"] == 0.9
        assert results[0]["document_id"] == 1
        assert results[0]["document_type"] == "resume"


class TestGetVectorStore:
    @patch("job_coach.ml.embeddings.vector_store.VectorStore")
    def test_get_vector_store_singleton(self, mock_vector_store_class):
        mock_instance = MagicMock()
        mock_vector_store_class.return_value = mock_instance

        # First call
        store1 = get_vector_store()
        assert store1 is mock_instance
        mock_vector_store_class.assert_called_once()

        # Second call should return same instance
        store2 = get_vector_store()
        assert store2 is mock_instance
        assert mock_vector_store_class.call_count == 1
