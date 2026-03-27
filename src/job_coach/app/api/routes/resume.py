from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from job_coach.app.api.dependencies import get_current_user
from job_coach.app.core.config import settings
from job_coach.app.core.logger import logger
from job_coach.app.db.dependencies import get_db
from job_coach.app.models.resume import Resume
from job_coach.app.models.user import User
from job_coach.app.schemas.resume import ResumeRead

router = APIRouter(tags=["resume"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.post("/upload", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a resume PDF. Stores metadata and optionally triggers indexing."""
    logger.info(f"User {current_user.id} uploading resume: {file.filename}")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(
            f"Upload failed: Unsupported file type '{file.content_type}' "
            f"for user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Only PDF is allowed.",
        )

    # Read file bytes
    pdf_bytes = await file.read()

    # Save metadata to DB
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename or "unnamed.pdf",
        content_type=file.content_type,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    logger.info(f"Stored resume metadata (ID: {resume.id}) for user {current_user.id}")

    # Save file to disk for Celery worker
    import os
    import uuid

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    # Try to queue the indexing task
    try:
        from job_coach.app.tasks.worker import index_resume_task

        # .delay() sends task to Celery asynchronously
        index_resume_task.delay(resume.id, file_path, current_user.id)
        logger.info(f"Queued indexing task for {resume.filename} (ID: {resume.id})")
    except ImportError as e:
        logger.warning(f"Skipped indexing task for {resume.filename}: {e}")
        pass  # Celery or ML deps not installed — skip indexing
    except Exception as e:
        logger.error(f"Failed to queue indexing task for {resume.filename}: {e}")
        pass  # Task queuing failed — resume metadata is still saved

    return resume


@router.get("/", response_model=list[ResumeRead])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all resumes uploaded by the current user."""
    logger.debug(f"User {current_user.id} requesting list of resumes")
    return db.query(Resume).filter(Resume.user_id == current_user.id).all()
