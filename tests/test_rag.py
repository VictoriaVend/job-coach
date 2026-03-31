"""Tests for RAG endpoint."""

from unittest.mock import patch

import pytest


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


@pytest.mark.asyncio
@patch("job_coach.app.api.routes.rag.run_rag_pipeline")
async def test_rag_query_configuration_error(mock_rag_pipeline, client, auth_headers):
    mock_rag_pipeline.side_effect = RuntimeError("config error")
    resp = await client.post(
        "/v1/rag/query",
        json={"query": "q", "top_k": 2},
        headers=auth_headers,
    )
    assert resp.status_code == 500


@pytest.mark.asyncio
@patch("job_coach.app.api.routes.rag.run_rag_pipeline")
async def test_rag_query_runtime_error(mock_rag_pipeline, client, auth_headers):
    mock_rag_pipeline.side_effect = Exception("fail")
    resp = await client.post(
        "/v1/rag/query",
        json={"query": "q", "top_k": 2},
        headers=auth_headers,
    )
    assert resp.status_code == 500
