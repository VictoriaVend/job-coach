"""Tests for analysis endpoints."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
@patch("job_coach.app.api.routes.analysis.analyze_resume_skills")
async def test_skill_gap_unauthenticated(mock_analyze, client):
    resp = await client.post(
        "/v1/analysis/skill-gap",
        json={"resume_text": "content", "target_role": "backend"},
    )
    assert resp.status_code == 401
    mock_analyze.assert_not_called()


@pytest.mark.asyncio
@patch("job_coach.app.api.routes.analysis.analyze_resume_skills")
async def test_skill_gap_success(mock_analyze, client, auth_headers):
    mock_analyze.return_value = {"skills": ["Python"], "gaps": []}
    resp = await client.post(
        "/v1/analysis/skill-gap",
        json={"resume_text": "content", "target_role": "backend"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"skills": ["Python"], "gaps": []}


@pytest.mark.asyncio
@patch("job_coach.app.api.routes.analysis.semantic_match")
async def test_semantic_match_unauthenticated(mock_semantic, client):
    resp = await client.post(
        "/v1/analysis/semantic-match",
        json={"resume_text": "a", "job_description": "b"},
    )
    assert resp.status_code == 401
    mock_semantic.assert_not_called()


@pytest.mark.asyncio
@patch("job_coach.app.api.routes.analysis.semantic_match")
async def test_semantic_match_success(mock_semantic, client, auth_headers):
    mock_semantic.return_value = {"score": 0.8, "missing": ["SQL"]}
    resp = await client.post(
        "/v1/analysis/semantic-match",
        json={"resume_text": "a", "job_description": "b"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"score": 0.8, "missing": ["SQL"]}
