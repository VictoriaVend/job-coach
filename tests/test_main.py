"""System endpoint tests for app startup, health, readiness, and headers."""

from unittest.mock import patch


def test_health_payload(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "AI-powered Job Coach"
    assert "debug" in data


def test_health_security_headers(client):
    resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" in resp.headers
    assert "X-XSS-Protection" in resp.headers


def test_readiness_ok(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "checks": {"database": "ok"}}


@patch("job_coach.app.main.engine.connect")
def test_readiness_degraded_on_db_error(mock_connect, client):
    mock_connect.side_effect = RuntimeError("db unavailable")

    resp = client.get("/ready")

    assert resp.status_code == 200
    assert resp.json() == {
        "status": "degraded",
        "checks": {"database": "error"},
    }
