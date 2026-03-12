"""Integration tests for analysis endpoints: /analysis/*."""

from unittest.mock import patch


def test_skill_gap_unauthenticated(client):
    resp = client.post(
        "/analysis/skill-gap",
        json={"resume_text": "Python", "job_description": "Java"},
    )
    assert resp.status_code == 401


@patch("job_coach.app.api.routes.analysis.analyze_skill_gap")
def test_skill_gap_success(mock_analyze, client, auth_headers):
    # Setup mock return value
    from job_coach.ml.analysis.skill_gap import SkillGapResult

    mock_analyze.return_value = SkillGapResult(
        resume_skills=["Python"],
        required_skills=["Python", "Docker"],
        matching_skills=["Python"],
        missing_skills=["Docker"],
        match_score=50.0,
    )

    resp = client.post(
        "/analysis/skill-gap",
        json={
            "resume_text": "I know Python",
            "job_description": "Need Python and Docker",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["match_score"] == 50.0
    assert "Docker" in data["missing_skills"]
    assert "Python" in data["matching_skills"]


def test_semantic_match_unauthenticated(client):
    resp = client.post(
        "/analysis/semantic-match",
        json={"resume_text": "Backend Dev", "job_description": "Senior Backend Eng"},
    )
    assert resp.status_code == 401


@patch("job_coach.app.api.routes.analysis.generate_semantic_match")
def test_semantic_match_success(mock_semantic, client, auth_headers):
    # Setup mock return value
    from job_coach.ml.analysis.semantic_match import SemanticMatchResult

    mock_semantic.return_value = SemanticMatchResult(
        similarity_score=85.5,
        interpretation="Excellent match. Highly aligned semantically.",
    )

    resp = client.post(
        "/analysis/semantic-match",
        json={"resume_text": "Backend Dev", "job_description": "Senior Backend Eng"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["similarity_score"] == 85.5
    assert "Excellent match" in data["interpretation"]
