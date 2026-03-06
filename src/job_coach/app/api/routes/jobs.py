from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from job_coach.app.api.dependencies import get_current_user
from job_coach.app.db.dependencies import get_db
from job_coach.app.models.user import User
from job_coach.app.schemas.job import JobCreate, JobRead, JobUpdate
from job_coach.app.services.job_service import (
    create_job,
    delete_job,
    get_job,
    get_jobs,
    update_job,
)

router = APIRouter(tags=["jobs"])


@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job_endpoint(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new job application."""
    return create_job(db, current_user.id, job_in)


@router.get("/", response_model=list[JobRead])
def list_jobs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all job applications for the current user."""
    return get_jobs(db, current_user.id, skip=skip, limit=limit)


@router.get("/{job_id}", response_model=JobRead)
def get_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific job application by ID."""
    job = get_job(db, job_id, current_user.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found",
        )
    return job


@router.patch("/{job_id}", response_model=JobRead)
def update_job_endpoint(
    job_id: int,
    job_in: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing job application."""
    job = update_job(db, job_id, current_user.id, job_in)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found",
        )
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a job application."""
    deleted = delete_job(db, job_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found",
        )
