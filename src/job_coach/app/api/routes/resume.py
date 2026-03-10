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

    # Try to index (extract text + embed) — graceful if ML deps not installed
    try:
        from job_coach.app.services.indexing_service import index_resume

        chunks_count = index_resume(db, resume.id, pdf_bytes, current_user.id)
        print(f"Indexed {chunks_count} chunks from {resume.filename}")
        db.refresh(resume)  # refresh to get raw_text
    except ImportError:
        pass  # ML dependencies not installed — skip indexing
    except Exception as e:
        print(f"Indexing failed: {e}")
        pass  # Indexing failed — resume metadata is still saved

    return resume


@router.get("/", response_model=list[ResumeRead])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all resumes uploaded by the current user."""
    return db.query(Resume).filter(Resume.user_id == current_user.id).all()
