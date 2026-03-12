"""Integration tests for RAG endpoints: /rag/*."""

from unittest.mock import patch


def test_rag_query_unauthenticated(client):
    resp = client.post(
        "/rag/query",
        json={"query": "What skills am I missing?", "top_k": 5},
    )
    assert resp.status_code == 401


@patch("job_coach.app.api.routes.rag.run_rag_pipeline")
def test_rag_query_success(mock_rag_pipeline, client, auth_headers):
    # Setup mock return value
    from job_coach.ml.rag.pipeline import RAGResult

    mock_rag_pipeline.return_value = RAGResult(
        query="What is my experience?",
        answer="You have 5 years of Python experience.",
        sources=["[Source 1] resume text chunk..."],
    )

    resp = client.post(
        "/rag/query",
        json={"query": "What is my experience?", "top_k": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "What is my experience?"
    assert data["answer"] == "You have 5 years of Python experience."
    assert len(data["sources"]) == 1
