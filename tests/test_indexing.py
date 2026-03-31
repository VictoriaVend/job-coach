"""Tests for background resume indexing lifecycle."""

from unittest.mock import AsyncMock, patch

import pytest

from job_coach.app.models.resume import Resume
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_index_resume_task_marks_completed(db):
    from job_coach.app.tasks import worker

    async def fake_index_resume(session, resume_id, file_path, user_id):
        return 3

    resume = Resume(
        user_id=1,
        filename="resume.pdf",
        content_type="application/pdf",
        status="UPLOADED",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    resume_id = resume.id

    with patch.object(worker, "SessionLocal", TestingSessionLocal), patch(
        "job_coach.app.services.indexing_service.index_resume",
        side_effect=fake_index_resume,
    ):
        result = worker.index_resume_task.run(
            resume_id, "C:/tmp/resume.pdf", resume.user_id
        )

    refreshed = await db.get(Resume, resume_id)
    assert refreshed is not None
    assert refreshed.status == "Indexed"
    assert result["chunks"] == 3


@pytest.mark.asyncio
async def test_index_resume_task_marks_failed_and_retries(db):
    from job_coach.app.tasks import worker

    async def fail_index_resume(*args, **kwargs):
        raise RuntimeError("parse failed")

    resume = Resume(
        user_id=1,
        filename="resume.pdf",
        content_type="application/pdf",
        status="UPLOADED",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    resume_id = resume.id

    retry_mock = AsyncMock(side_effect=RuntimeError("retry scheduled"))

    with patch.object(worker, "SessionLocal", TestingSessionLocal), patch(
        "job_coach.app.services.indexing_service.index_resume",
        side_effect=fail_index_resume,
    ), patch.object(worker.index_resume_task, "retry", retry_mock):
        with pytest.raises(RuntimeError, match="retry scheduled"):
            worker.index_resume_task.run(resume_id, "C:/tmp/resume.pdf", resume.user_id)

    refreshed = await db.get(Resume, resume_id)
    assert refreshed is not None
    assert refreshed.status == "FAILED"
    retry_mock.assert_called_once()
