"""Tests for job application CRUD: /jobs/."""


class TestCreateJob:
    def test_create_job(self, client, auth_headers):
        resp = client.post(
            "/v1/jobs/",
            json={
                "company": "Google",
                "position": "Backend Engineer",
                "status": "Applied",
                "url": "https://careers.google.com/123",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["company"] == "Google"
        assert data["position"] == "Backend Engineer"
        assert data["status"] == "Applied"
        assert data["url"] == "https://careers.google.com/123"
        assert "id" in data

    def test_create_job_minimal(self, client, auth_headers):
        resp = client.post(
            "/v1/jobs/",
            json={"company": "Meta", "position": "SWE"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "Applied"  # default
        assert resp.json()["url"] is None

    def test_create_job_unauthenticated(self, client):
        resp = client.post(
            "/v1/jobs/",
            json={"company": "X", "position": "Y"},
        )
        assert resp.status_code == 401


class TestListJobs:
    def test_list_empty(self, client, auth_headers):
        resp = client.get("/v1/jobs/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_own_jobs(self, client, auth_headers):
        # Create 2 jobs
        client.post(
            "/v1/jobs/",
            json={"company": "A", "position": "Dev"},
            headers=auth_headers,
        )
        client.post(
            "/v1/jobs/",
            json={"company": "B", "position": "SRE"},
            headers=auth_headers,
        )
        resp = client.get("/v1/jobs/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestGetJob:
    def test_get_job_by_id(self, client, auth_headers):
        create_resp = client.post(
            "/v1/jobs/",
            json={"company": "Netflix", "position": "ML Eng"},
            headers=auth_headers,
        )
        job_id = create_resp.json()["id"]

        resp = client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["company"] == "Netflix"

    def test_get_nonexistent_job(self, client, auth_headers):
        resp = client.get("/v1/jobs/9999", headers=auth_headers)
        assert resp.status_code == 404


class TestUpdateJob:
    def test_update_status(self, client, auth_headers):
        create_resp = client.post(
            "/v1/jobs/",
            json={"company": "Amazon", "position": "SDE"},
            headers=auth_headers,
        )
        job_id = create_resp.json()["id"]

        resp = client.patch(
            f"/v1/jobs/{job_id}",
            json={"status": "Interview"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "Interview"
        assert resp.json()["company"] == "Amazon"  # unchanged

    def test_update_nonexistent(self, client, auth_headers):
        resp = client.patch(
            "/v1/jobs/9999",
            json={"status": "Offer"},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestDeleteJob:
    def test_delete_job(self, client, auth_headers):
        create_resp = client.post(
            "/v1/jobs/",
            json={"company": "Apple", "position": "iOS Dev"},
            headers=auth_headers,
        )
        job_id = create_resp.json()["id"]

        resp = client.delete(f"/v1/jobs/{job_id}", headers=auth_headers)
        assert resp.status_code == 204

        # Verify it's gone
        resp = client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_nonexistent(self, client, auth_headers):
        resp = client.delete("/v1/jobs/9999", headers=auth_headers)
        assert resp.status_code == 404
