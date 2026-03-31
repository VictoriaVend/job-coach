"""Security tests: Cross-user isolation (IDOR) and headers."""

import io

import pytest


class TestIDORIsolation:
    @pytest.mark.asyncio
    async def test_user_cannot_get_other_user_job(
        self, client, auth_headers, other_auth_headers
    ):
        create_resp = await client.post(
            "/v1/jobs/",
            json={"company": "Secret Corp", "position": "Spy"},
            headers=other_auth_headers,
        )
        job_id = create_resp.json()["id"]

        evil_resp = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
        assert evil_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_user_cannot_delete_other_user_job(
        self, client, auth_headers, other_auth_headers
    ):
        create_resp = await client.post(
            "/v1/jobs/",
            json={"company": "Target", "position": "Dev"},
            headers=other_auth_headers,
        )
        job_id = create_resp.json()["id"]

        evil_resp = await client.delete(f"/v1/jobs/{job_id}", headers=auth_headers)
        assert evil_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_user_cannot_list_other_user_resumes(
        self, client, auth_headers, other_auth_headers
    ):
        fake_pdf = io.BytesIO(b"%PDF-1.4 test")
        await client.post(
            "/v1/resume/upload",
            files={"file": ("secret.pdf", fake_pdf, "application/pdf")},
            headers=other_auth_headers,
        )

        resp = await client.get("/v1/resume/", headers=auth_headers)
        assert len(resp.json()) == 0


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_security_headers_present(self, client):
        resp = await client.get("/health")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in resp.headers
        assert "X-XSS-Protection" in resp.headers


class TestInputValidation:
    @pytest.mark.asyncio
    async def test_list_jobs_limit_cap(self, client, auth_headers):
        resp = await client.get("/v1/jobs/?limit=600", headers=auth_headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_rag_top_k_cap(self, client, auth_headers):
        resp = await client.post(
            "/v1/rag/query",
            json={"query": "test", "top_k": 50},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_analysis_payload_limit(self, client, auth_headers):
        huge_text = "a" * 60_000
        resp = await client.post(
            "/v1/analysis/skill-gap",
            json={"resume_text": huge_text, "job_description": "short"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestAuthGuards:
    @pytest.mark.asyncio
    async def test_invalid_token_payload_is_rejected(self, client):
        resp = await client.get(
            "/v1/jobs/",
            headers={"Authorization": "Bearer definitely-not-a-real-token"},
        )
        assert resp.status_code == 401
