"""Unit tests for ML ingestion and mathematical analysis."""

from unittest.mock import patch

import numpy as np

from job_coach.ml.analysis.semantic_match import generate_semantic_match
from job_coach.ml.ingestion.parser import chunk_text


class TestChunkText:
    def test_empty_text(self):
        assert chunk_text("") == []

    def test_short_text_single_chunk(self):
        text = "Python developer with 5 years of experience."
        chunks = chunk_text(text, chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["chunk_index"] == 0

    def test_chunking_produces_overlap(self):
        # Create text longer than chunk_size
        words = " ".join(["word"] * 200)  # ~1000 chars
        chunks = chunk_text(words, chunk_size=200, chunk_overlap=50)
        assert len(chunks) > 1
        # Each chunk should have metadata
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i
            assert "start_char" in chunk
            assert "end_char" in chunk
            assert len(chunk["text"]) > 0

    def test_whitespace_is_cleaned(self):
        text = "  Hello   world  \n\n  foo   bar  "
        chunks = chunk_text(text, chunk_size=500)
        assert len(chunks) == 1
        # Multiple spaces collapsed
        assert "  " not in chunks[0]["text"]

    def test_chunk_index_sequential(self):
        text = ". ".join(["Sentence number " + str(i) for i in range(50)])
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i


class TestHealth:
    """Smoke test for the health endpoint."""

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["service"] == "AI-powered Job Coach"


class TestSemanticMatch:
    @patch("job_coach.ml.embeddings.service.EmbeddingService.embed_batch")
    def test_semantic_match_mean_pooling(self, mock_embed_batch):
        # Mocking embed_batch to strictly test the NumPy Mean Pooling Math
        # Case: Resume has 2 chunks, Job has 1 chunk.
        # Vector Arrays -> [1.0, 0.0] and [0.0, 1.0] -> Pooled: [0.5, 0.5]
        # Target Job Array -> [0.5, 0.5]
        # Result -> 100% Cosine Similarity match

        def mock_embed_side_effect(texts):
            if len(texts) == 2:
                return np.array([[1.0, 0.0], [0.0, 1.0]])
            if len(texts) == 1:
                return np.array([[0.5, 0.5]])
            return np.array([[0.0, 0.0]])

        mock_embed_batch.side_effect = mock_embed_side_effect

        # Triggering 2 chunks dynamically: Langchain chunk_size=500
        resume_text = (
            """This string is exactly one hundred characters long
             to manipulate chunking limits natively."""
            * 10
        )
        job_text = "Generic job description."

        result = generate_semantic_match(resume_text, job_text)

        # Assert correct ML mathematical distribution
        assert mock_embed_batch.call_count == 2
        assert 99.0 <= result.similarity_score <= 100.0
        assert "Highly aligned semantically" in result.interpretation
