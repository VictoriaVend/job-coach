from sqlalchemy.orm import Session

from job_coach.app.core.logger import logger
from job_coach.app.core.security import hash_password, verify_password
from job_coach.app.models.user import User
from job_coach.app.schemas.user import UserCreate


def get_user_by_username(db: Session, username: str) -> User | None:
    logger.debug(f"DB Query: Fetching user by username: {username}")
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    logger.debug(f"DB Query: Fetching user by email: {email}")
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    logger.debug(f"DB Query: Fetching user by id: {user_id}")
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created new user: {user.username}")
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)
    if not user:
        logger.warning(f"Authentication failed for user: {username}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed for user: {username}")
        return None
    logger.info(f"User {username} successfully authenticated")
    return user
