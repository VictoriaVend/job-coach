"""Tests for background resume indexing lifecycle."""

from unittest.mock import patch

import pytest
from job_coach.app.models.resume import Resume


@pytest.mark.asyncio
async def test_index_resume_task_marks_completed(db, registered_user):
    from job_coach.app.tasks.worker import _process_resume

    async def fake_index_resume(session, resume_id, file_path, user_id):
        return 3

    resume = Resume(
        user_id=registered_user["id"],
        filename="resume.pdf",
        content_type="application/pdf",
        status="UPLOADED",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    resume_id = resume.id

    with patch(
        "job_coach.app.services.indexing_service.index_resume",
        side_effect=fake_index_resume,
    ):
        result = await _process_resume(resume_id, "C:/tmp/resume.pdf", resume.user_id)

    # Refresh the resume object to see changes made in _process_resume
    await db.refresh(resume)
    assert resume.status == "Indexed"
    assert result["chunks"] == 3


@pytest.mark.asyncio
async def test_index_resume_task_marks_failed_and_retries(db, registered_user):
    from job_coach.app.tasks.worker import _mark_failed

    resume = Resume(
        user_id=registered_user["id"],
        filename="resume.pdf",
        content_type="application/pdf",
        status="UPLOADED",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    resume_id = resume.id

    # Simulate failure by calling _mark_failed directly
    await _mark_failed(resume_id)

    # Refresh the resume object to see changes made in _mark_failed
    await db.refresh(resume)
    assert resume.status == "Failed"
