"""Celery background tasks for long-running operations."""

import logging

from job_coach.app.core.celery import celery_app
from job_coach.app.db.session import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="job_coach.app.tasks.index_resume_task", bind=True, max_retries=3)
def index_resume_task(self, resume_id: int, file_path: str, user_id: int) -> dict:
    """Background task to parse and index a PDF resume."""
    from job_coach.app.services.indexing_service import index_resume

    logger.info(f"Starting indexing for resume {resume_id} at {file_path}")

    db = SessionLocal()
    try:
        chunks_count = index_resume(db, resume_id, file_path, user_id)
        logger.info(
            f"Successfully indexed {chunks_count} chunks for resume {resume_id}"
        )
        return {"status": "success", "resume_id": resume_id, "chunks": chunks_count}
    except Exception as exc:
        logger.error(f"Error indexing resume {resume_id}: {exc}")
        # Retry with exponential backoff if needed,
        # though parsing usually fails deterministically
        raise self.retry(exc=exc, countdown=2**self.request.retries)
    finally:
        db.close()
