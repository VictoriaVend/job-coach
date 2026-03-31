"""Tests for resume endpoints: upload, listing, and indexing visibility."""

import io
from unittest.mock import patch

import pytest


class TestResumeUpload:
    @pytest.mark.asyncio
    async def test_upload_rejects_non_pdf(self, client, auth_headers):
        fake_file = io.BytesIO(b"not a pdf")
        resp = await client.post(
            "/v1/resume/upload",
            files={"file": ("test.txt", fake_file, "text/plain")},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "Only PDF" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_rejects_spoofed_pdf(self, client, auth_headers):
        fake_pdf = io.BytesIO(b"not really a pdf")
        resp = await client.post(
            "/v1/resume/upload",
            files={"file": ("resume.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "File content does not match PDF format" in resp.json()["detail"]

    @pytest.mark.asyncio
    @patch("job_coach.app.tasks.worker.index_resume_task.delay")
    async def test_upload_pdf_stores_metadata(self, mock_delay, client, auth_headers):
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
        resp = await client.post(
            "/v1/resume/upload",
            files={"file": ("resume.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["filename"] == "resume.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["status"] == "Uploaded"
        assert data["raw_text"] is None
        assert "id" in data
        mock_delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_unauthenticated(self, client):
        fake_pdf = io.BytesIO(b"%PDF-1.4")
        resp = await client.post(
            "/v1/resume/upload",
            files={"file": ("cv.pdf", fake_pdf, "application/pdf")},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, client, auth_headers):
        large_file = io.BytesIO(b"0" * (60 * 1024 * 1024))
        resp = await client.post(
            "/v1/resume/upload",
            files={"file": ("large.pdf", large_file, "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 413
        assert "File size exceeds the 50MB limit" in resp.json()["detail"]


class TestResumeList:
    @pytest.mark.asyncio
    async def test_list_empty(self, client, auth_headers):
        resp = await client.get("/v1/resume/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    @patch("job_coach.app.tasks.worker.index_resume_task.delay")
    async def test_list_after_upload(self, mock_delay, client, auth_headers):
        fake_pdf = io.BytesIO(b"%PDF-1.4 content")
        upload_resp = await client.post(
            "/v1/resume/upload",
            files={"file": ("r1.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
        resume_id = upload_resp.json()["id"]

        resp = await client.get("/v1/resume/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["filename"] == "r1.pdf"
        assert resp.json()[0]["status"] == "Uploaded"
        mock_delay.assert_called_once()

        detail_resp = await client.get(f"/v1/resume/{resume_id}", headers=auth_headers)
        assert detail_resp.status_code == 200
        assert detail_resp.json()["id"] == resume_id

    @pytest.mark.asyncio
    async def test_get_resume_not_found(self, client, auth_headers):
        resp = await client.get("/v1/resume/999", headers=auth_headers)
        assert resp.status_code == 404
