from sqlalchemy.orm import Session

from job_coach.app.core.logger import logger
from job_coach.app.models.applications import JobApplication
from job_coach.app.schemas.job import JobCreate, JobUpdate


def create_job(db: Session, user_id: int, job_in: JobCreate) -> JobApplication:
    job = JobApplication(user_id=user_id, **job_in.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(f"User {user_id} created new job application {job.id}")
    return job


def get_jobs(
    db: Session, user_id: int, skip: int = 0, limit: int = 50
) -> list[JobApplication]:
    return (
        db.query(JobApplication)
        .filter(JobApplication.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_job(db: Session, job_id: int, user_id: int) -> JobApplication | None:
    return (
        db.query(JobApplication)
        .filter(JobApplication.id == job_id, JobApplication.user_id == user_id)
        .first()
    )


def update_job(
    db: Session, job_id: int, user_id: int, job_in: JobUpdate
) -> JobApplication | None:
    job = get_job(db, job_id, user_id)
    if not job:
        return None
    for field, value in job_in.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    logger.info(f"User {user_id} updated job application {job_id}")
    return job


def delete_job(db: Session, job_id: int, user_id: int) -> bool:
    job = get_job(db, job_id, user_id)
    if not job:
        return False
    db.delete(job)
    db.commit()
    logger.info(f"User {user_id} deleted job application {job_id}")
    return True
