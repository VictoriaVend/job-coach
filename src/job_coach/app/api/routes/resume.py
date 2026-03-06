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
def upload_resume(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a resume PDF. Text extraction and embedding happen asynchronously."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Only PDF is allowed.",
        )

    # TODO: Save file to storage (S3 / local) and trigger Celery task for
    #       text extraction + embedding. For now, store metadata only.
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename or "unnamed.pdf",
        content_type=file.content_type,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/", response_model=list[ResumeRead])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all resumes uploaded by the current user."""
    return db.query(Resume).filter(Resume.user_id == current_user.id).all()
