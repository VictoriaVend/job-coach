from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from job_coach.app.core.config import settings
from job_coach.app.core.logger import logger

# Workaround for passlib + bcrypt==4.x/5.x incompatibility
# passlib expects bcrypt.__about__.__version__, which is missing in newer bcrypt versions
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("About", (), {"__version__": bcrypt.__version__})

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    logger.debug("Hashing new password")
    if len(password.encode("utf-8")) > 72:
        logger.error("Password hashing failed: payload exceeds 72 bytes")
        raise ValueError("Password too long (max 72 bytes)")
    return pwd_context.hash(secret=password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug("Verifying password hash")
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug(f"Created access token for user {data.get('sub')}")
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """Decode JWT token. Returns payload dict or None if invalid."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        logger.warning(f"JWT Decode Error: {e}")
        return None
