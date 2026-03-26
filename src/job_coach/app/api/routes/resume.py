import re
import uuid
from pathlib import Path

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
PDF_MAGIC_BYTES = b"%PDF"

_UPLOAD_DIR = Path(settings.UPLOAD_DIR)


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

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit

    # Check file size before loading into memory
    file.file.seek(0, 2)
    file_size = file.file.tell()
    await file.seek(0)

    if file_size > MAX_FILE_SIZE:
        logger.warning(
            f"Upload rejected: File too large ({file_size} bytes) "
            f"for user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File too large. Maximum allowed size is 5MB.",
        )

    # Read file bytes safely now that size is bounded
    pdf_bytes = await file.read()

    # Validate PDF magic bytes — defence against Content-Type spoofing
    if not pdf_bytes.startswith(PDF_MAGIC_BYTES):
        logger.warning(
            f"Upload rejected: file does not start with PDF magic bytes "
            f"for user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not appear to be a valid PDF.",
        )

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
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Sanitize filename to prevent Path Traversal
    safe_filename = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", file.filename or "unnamed.pdf")
    unique_filename = f"{uuid.uuid4()}_{safe_filename}"
    file_path = _UPLOAD_DIR / unique_filename

    # Anchor check: ensure resolved path stays within upload directory
    resolved = file_path.resolve()
    if not str(resolved).startswith(str(_UPLOAD_DIR.resolve())):
        logger.error(f"Path traversal attempt detected for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    with open(resolved, "wb") as f:
        f.write(pdf_bytes)

    logger.info(
        f"Saved resume {resume.id} for user {current_user.id} to {resolved.name}"
    )

    # Try to queue the indexing task
    try:
        from job_coach.app.tasks.worker import index_resume_task

        index_resume_task.delay(resume.id, str(resolved), current_user.id)
        logger.info(f"Queued indexing task for {resume.filename}" f" (ID: {resume.id})")
    except ImportError as e:
        logger.warning(f"Skipped indexing task for {resume.filename}: {e}")
    except Exception:
        logger.exception(f"Failed to queue indexing task for {resume.filename}")

    return resume


@router.get("/", response_model=list[ResumeRead])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all resumes uploaded by the current user."""
    logger.debug(f"User {current_user.id} requesting list of resumes")
    return db.query(Resume).filter(Resume.user_id == current_user.id).all()


@router.get("/{resume_id}", response_model=ResumeRead)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single resume with indexing status for the current user."""
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    return resume
