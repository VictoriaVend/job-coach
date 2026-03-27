"""Celery background tasks for long-running operations."""

from job_coach.app.core.celery import celery_app
from job_coach.app.core.logger import logger
from job_coach.app.db.session import SessionLocal


@celery_app.task(name="job_coach.app.tasks.index_resume_task", bind=True, max_retries=3)
def index_resume_task(self, resume_id: int, file_path: str, user_id: int) -> dict:
    """Background task to parse and index a PDF resume."""
    from job_coach.app.services.indexing_service import index_resume

    logger.info("Starting indexing for resume %s at %s", resume_id, file_path)

    db = SessionLocal()
    from job_coach.app.models.resume import Resume

    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.status = "PROCESSING"
            db.commit()

        chunks_count = index_resume(db, resume_id, file_path, user_id)

        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.status = "COMPLETED"
            db.commit()

        logger.info(
            "Successfully indexed %s chunks for resume %s", chunks_count, resume_id
        )
        return {"status": "success", "resume_id": resume_id, "chunks": chunks_count}
    except Exception as exc:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.status = "FAILED"
            db.commit()

        logger.error("Error indexing resume %s: %s", resume_id, exc)
        # Retry with exponential backoff if needed,
        # though parsing usually fails deterministically
        raise self.retry(exc=exc, countdown=2**self.request.retries)
    finally:
        db.close()
