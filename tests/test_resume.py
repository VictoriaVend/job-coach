"""Tests for resume endpoints: /resume/."""

import io


class TestResumeUpload:
    def test_upload_rejects_non_pdf(self, client, auth_headers):
        fake_file = io.BytesIO(b"not a pdf")
        resp = client.post(
            "/resume/upload",
            files={"file": ("test.txt", fake_file, "text/plain")},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "Only PDF" in resp.json()["detail"]

    def test_upload_pdf_stores_metadata(self, client, auth_headers):
        # Minimal valid PDF bytes (header only — won't parse, but passes content_type)
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
        resp = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["filename"] == "resume.pdf"
        assert data["content_type"] == "application/pdf"
        assert "id" in data

    def test_upload_unauthenticated(self, client):
        fake_pdf = io.BytesIO(b"%PDF-1.4")
        resp = client.post(
            "/resume/upload",
            files={"file": ("cv.pdf", fake_pdf, "application/pdf")},
        )
        assert resp.status_code == 401


class TestResumeList:
    def test_list_empty(self, client, auth_headers):
        resp = client.get("/resume/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_upload(self, client, auth_headers):
        fake_pdf = io.BytesIO(b"%PDF-1.4 content")
        client.post(
            "/resume/upload",
            files={"file": ("r1.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
        resp = client.get("/resume/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["filename"] == "r1.pdf"
