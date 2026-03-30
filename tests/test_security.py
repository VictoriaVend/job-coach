"""Security tests: Cross-user isolation (IDOR) and headers."""

import io


class TestIDORIsolation:
    def test_user_cannot_get_other_user_job(
        self, client, auth_headers, other_auth_headers
    ):
        # 1. User B (other) creates a job
        create_resp = client.post(
            "/v1/jobs/",
            json={"company": "Secret Corp", "position": "Spy"},
            headers=other_auth_headers,
        )
        job_id = create_resp.json()["id"]

        # 2. User A (auth) tries to GET User B's job
        evil_resp = client.get(f"/v1/jobs/{job_id}", headers=auth_headers)

        # Should be 404 (not found) or 403 (forbidden).
        # Current implementation returns 404 for missing/belonging to another user (security by obscurity in errors).
        assert evil_resp.status_code == 404

    def test_user_cannot_delete_other_user_job(
        self, client, auth_headers, other_auth_headers
    ):
        create_resp = client.post(
            "/v1/jobs/",
            json={"company": "Target", "position": "Dev"},
            headers=other_auth_headers,
        )
        job_id = create_resp.json()["id"]

        evil_resp = client.delete(f"/v1/jobs/{job_id}", headers=auth_headers)
        assert evil_resp.status_code == 404

    def test_user_cannot_list_other_user_resumes(
        self, client, auth_headers, other_auth_headers
    ):
        # User B uploads a resume
        fake_pdf = io.BytesIO(b"%PDF-1.4 test")
        client.post(
            "/v1/resume/upload",
            files={"file": ("secret.pdf", fake_pdf, "application/pdf")},
            headers=other_auth_headers,
        )

        # User A lists resumes
        resp = client.get("/v1/resume/", headers=auth_headers)
        # Should be empty for User A
        assert len(resp.json()) == 0


class TestSecurityHeaders:
    def test_security_headers_present(self, client):
        resp = client.get("/health")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in resp.headers
        assert "X-XSS-Protection" in resp.headers


class TestInputValidation:
    def test_list_jobs_limit_cap(self, client, auth_headers):
        # Requesting limit=999 should be capped or rejected.
        # Implementation adds Query(le=500). FastAPI returns 422 if exceeds.
        resp = client.get("/v1/jobs/?limit=600", headers=auth_headers)
        assert resp.status_code == 422

    def test_rag_top_k_cap(self, client, auth_headers):
        # Field(le=20) constraint
        resp = client.post(
            "/v1/rag/query",
            json={"query": "test", "top_k": 50},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_analysis_payload_limit(self, client, auth_headers):
        # max_length=50_000
        huge_text = "a" * 60_000
        resp = client.post(
            "/v1/analysis/skill-gap",
            json={"resume_text": huge_text, "job_description": "short"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestAuthGuards:
    def test_invalid_token_payload_is_rejected(self, client):
        resp = client.get(
            "/v1/jobs/",
            headers={"Authorization": "Bearer definitely-not-a-real-token"},
        )
        assert resp.status_code == 401
