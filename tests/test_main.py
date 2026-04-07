"""System endpoint tests for app startup, health, readiness, and headers."""

from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.asyncio
async def test_health_payload(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "AI-powered Job Coach"
    # Also check security headers
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" in resp.headers
    assert "X-XSS-Protection" in resp.headers


@pytest.mark.asyncio
async def test_readiness_ok(client):
    resp = await client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "checks": {"database": "ok"}}


@pytest.mark.asyncio
async def test_readiness_degraded_on_db_error(client):
    class MockConnection:
        async def __aenter__(self):
            raise RuntimeError("db unavailable")

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

    mock_engine = AsyncMock()
    mock_engine.connect = Mock(return_value=MockConnection())

    with patch("job_coach.app.main.async_engine", mock_engine):
        resp = await client.get("/ready")

    assert resp.status_code == 200
    assert resp.json() == {
        "status": "degraded",
        "checks": {"database": "error"},
        "reason": "Database connection timeout or failure",
    }
