"""Integration tests for RAG endpoints: /rag/*."""

from unittest.mock import patch


def test_rag_query_unauthenticated(client):
    resp = client.post(
        "/v1/rag/query",
        json={"query": "What skills am I missing?", "top_k": 5},
    )
    assert resp.status_code == 401


@patch("job_coach.ml.rag.run_rag_pipeline")
def test_rag_query_success(mock_rag_pipeline, client, auth_headers):
    from job_coach.ml.rag.pipeline import RAGResult

    mock_rag_pipeline.return_value = RAGResult(
        query="What is my experience?",
        answer="You have 5 years of Python experience.",
        sources=[
            {
                "text": "[Source 1] resume text chunk...",
                "score": 0.9123,
                "document_id": 42,
                "document_type": "resume",
                "chunk_index": 0,
            }
        ],
    )

    resp = client.post(
        "/v1/rag/query",
        json={"query": "What is my experience?", "top_k": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "What is my experience?"
    assert data["answer"] == "You have 5 years of Python experience."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["document_type"] == "resume"
    assert data["sources"][0]["score"] == 0.9123


@patch("job_coach.ml.rag.run_rag_pipeline")
def test_rag_query_configuration_error(mock_rag_pipeline, client, auth_headers):
    from job_coach.ml.rag.pipeline import RAGConfigurationError

    mock_rag_pipeline.side_effect = RAGConfigurationError(
        "HUGGINGFACEHUB_API_TOKEN is not configured for real RAG inference."
    )

    resp = client.post(
        "/v1/rag/query",
        json={"query": "What is my experience?", "top_k": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 503
    assert "HUGGINGFACEHUB_API_TOKEN" in resp.json()["detail"]


@patch("job_coach.ml.rag.run_rag_pipeline")
def test_rag_query_runtime_error(mock_rag_pipeline, client, auth_headers):
    from job_coach.ml.rag.pipeline import RAGExecutionError

    mock_rag_pipeline.side_effect = RAGExecutionError(
        "Failed to retrieve context from Qdrant: connection refused"
    )

    resp = client.post(
        "/v1/rag/query",
        json={"query": "What is my experience?", "top_k": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 503
    assert "Qdrant" in resp.json()["detail"]
