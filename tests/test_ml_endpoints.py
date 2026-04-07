"""Tests for ML-powered endpoints: analysis and RAG."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_skill_gap_unauthenticated(client):
    # Testing unauthenticated request - it should fail BEFORE calling ML service
    resp = await client.post(
        "/v1/analysis/skill-gap",
        json={"resume_text": "content", "job_description": "backend"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_skill_gap_success(client, auth_headers):
    # Mocking the ML service called inside the route
    mock_result = MagicMock()
    mock_result.resume_skills = ["Python"]
    mock_result.required_skills = ["Python", "SQL"]
    mock_result.matching_skills = ["Python"]
    mock_result.missing_skills = ["SQL"]
    mock_result.match_score = 50.0

    with patch("job_coach.ml.analysis.analyze_skill_gap", return_value=mock_result):
        resp = await client.post(
            "/v1/analysis/skill-gap",
            json={"resume_text": "content", "job_description": "backend"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_score"] == 50.0
        assert "Python" in data["matching_skills"]


@pytest.mark.asyncio
async def test_semantic_match_unauthenticated(client):
    resp = await client.post(
        "/v1/analysis/semantic-match",
        json={"resume_text": "a", "job_description": "b"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_semantic_match_success(client, auth_headers):
    mock_result = MagicMock()
    mock_result.similarity_score = 0.8
    mock_result.interpretation = "Good match"

    with patch(
        "job_coach.ml.analysis.semantic_match.generate_semantic_match",
        return_value=mock_result,
    ):
        resp = await client.post(
            "/v1/analysis/semantic-match",
            json={"resume_text": "a", "job_description": "b"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["similarity_score"] == 0.8


@pytest.mark.asyncio
async def test_rag_query_unauthenticated(client):
    resp = await client.post(
        "/v1/rag/query",
        json={"query": "What skills do I need?", "top_k": 3},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
@patch("job_coach.app.api.routes.rag.run_rag_pipeline")
async def test_rag_query_success(mock_rag_pipeline, client, auth_headers):
    mock_rag_pipeline.return_value = {"answer": "test", "sources": []}
    resp = await client.post(
        "/v1/rag/query",
        json={"query": "How to improve resume?", "top_k": 2},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"answer": "test", "sources": []}
