"""System endpoint tests for app startup, health, readiness, and headers."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_health_payload(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "AI-powered Job Coach"
    assert "debug" in data


@pytest.mark.asyncio
async def test_health_security_headers(client):
    resp = await client.get("/health")
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
    async_mock = AsyncMock()
    async_mock.__aenter__.side_effect = RuntimeError("db unavailable")
    async_mock.__aexit__.return_value = False

    with patch("job_coach.app.main.engine.connect", return_value=async_mock):
        resp = await client.get("/ready")

    assert resp.status_code == 200
    assert resp.json() == {
        "status": "degraded",
        "checks": {"database": "error"},
    }
