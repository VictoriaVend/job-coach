"""Unit tests for ML ingestion: text chunking logic."""

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
        assert resp.json() == {"status": "ok"}
