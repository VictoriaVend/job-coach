from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from job_coach.app.api.dependencies import get_current_user
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
    if file.content_type not in ALLOWED_CONTENT_TYPES:
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

    # Save file to disk for Celery worker
    import os
    import uuid

    upload_dir = os.path.join("uploads", "resumes")
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
        print(f"Queued indexing task for {resume.filename}")
    except ImportError:
        pass  # Celery or ML deps not installed — skip indexing
    except Exception as e:
        print(f"Failed to queue indexing task: {e}")
        pass  # Task queuing failed — resume metadata is still saved

    return resume


@router.get("/", response_model=list[ResumeRead])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all resumes uploaded by the current user."""
    return db.query(Resume).filter(Resume.user_id == current_user.id).all()
