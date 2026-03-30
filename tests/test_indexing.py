"""Tests for background resume indexing lifecycle."""

from unittest.mock import patch

from job_coach.app.models.resume import Resume


@patch("job_coach.app.tasks.worker.SessionLocal")
@patch("job_coach.app.services.indexing_service.index_resume")
def test_index_resume_task_marks_completed(mock_index_resume, mock_session_local, db):
    from job_coach.app.tasks.worker import index_resume_task

    mock_session_local.return_value = db
    mock_index_resume.return_value = 3
    resume = Resume(
        user_id=1,
        filename="resume.pdf",
        content_type="application/pdf",
        status="UPLOADED",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    resume_id = resume.id

    index_resume_task.run(resume_id, "C:/tmp/resume.pdf", resume.user_id)

    refreshed = db.query(Resume).filter(Resume.id == resume_id).first()
    assert refreshed is not None
    assert refreshed.status == "Indexed"


@patch("job_coach.app.tasks.worker.SessionLocal")
@patch("job_coach.app.services.indexing_service.index_resume")
@patch("job_coach.app.tasks.worker.index_resume_task.retry")
def test_index_resume_task_marks_failed_and_retries(
    mock_retry, mock_index_resume, mock_session_local, db
):
    from job_coach.app.tasks.worker import index_resume_task

    mock_session_local.return_value = db
    mock_index_resume.side_effect = RuntimeError("parse failed")
    mock_retry.side_effect = RuntimeError("retry scheduled")

    resume = Resume(
        user_id=1,
        filename="resume.pdf",
        content_type="application/pdf",
        status="UPLOADED",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    resume_id = resume.id

    try:
        index_resume_task.run(resume_id, "C:/tmp/resume.pdf", resume.user_id)
    except RuntimeError as exc:
        assert str(exc) == "retry scheduled"

    refreshed = db.query(Resume).filter(Resume.id == resume_id).first()
    assert refreshed is not None
    assert refreshed.status == "FAILED"
    mock_retry.assert_called_once()
