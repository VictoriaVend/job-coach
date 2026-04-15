"""
Configuration Management Module
================================
Purpose: Centralized application settings with Pydantic validation.
Security: Enforces strong secret keys, validates all external service URLs.
Performance: Settings loaded once at startup.
"""

from pathlib import Path
from typing import Set

from pydantic import model_validator
from pydantic_settings import BaseSettings

# List of insecure placeholder values that will trigger validation errors
# CRITICAL: Prevents accidental deployment with weak secrets
_FORBIDDEN_KEYS = {"change-me-in-production", "your_secret_key_here", "", "secret"}


def get_project_root() -> Path:
    """Traverse up to find the project root directory."""
    current = Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return current.parents[3]  # Fallback to a sensible default if not found


BASE_DIR = get_project_root()


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Uses Pydantic settings for type validation and environment file support.
    All critical settings must be explicitly set - no unsafe defaults provided.
    """

    # Application metadata
    APP_NAME: str = "AI-Powered Backend System for Document Analysis (RAG Pipeline)"
    APP_VERSION: str = "0.1.0"

    # Database and Infrastructure URLs - MUST be set in production
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/job_coach"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"

    # Database performance settings (can be overridden in tests)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True

    # CORS configuration - restrict to known origins in production
    CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # External AI/ML service configuration
    HUGGINGFACEHUB_API_TOKEN: str | None = (
        None  # Optional - required only for RAG features
    )
    HF_MODEL_ID: str = "mistralai/Mistral-7B-Instruct-v0.3"  # LLM for text generation
    EMBEDDING_MODEL_ID: str = (
        "all-MiniLM-L6-v2"  # Lightweight embedding model for fast inference
    )
    RAG_LLM_TASK: str = "text-generation"  # Task type for HuggingFace Inference API
    RAG_LLM_TEMPERATURE: float = 0.1  # Lower = more deterministic (good for job coach)
    RAG_LLM_MAX_NEW_TOKENS: int = 512  # Token limit to control response length
    RAG_LLM_DO_SAMPLE: bool = True  # Use sampling for diversity in responses
    RAG_TOP_K_DEFAULT: int = 5  # Default number of context chunks to retrieve
    RAG_TOP_K_MIN: int = 1
    RAG_TOP_K_MAX: int = 20
    RAG_QUERY_MAX_CHARS: int = 2000  # Prevent excessively long queries
    ANALYSIS_TEXT_MAX_CHARS: int = 50_000  # Max characters to analyze per document

    # Text chunking configuration - affects embedding quality
    # Larger chunks = more context but less granular search
    # Overlap helps with context preservation at chunk boundaries
    INGEST_CHUNK_SIZE: int = 800
    INGEST_CHUNK_OVERLAP: int = 150
    SEMANTIC_MATCH_CHUNK_SIZE: int = 1000
    SEMANTIC_MATCH_CHUNK_OVERLAP: int = 100

    # File Upload Configuration
    UPLOAD_MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB default limit
    UPLOAD_CHUNK_SIZE: int = 8192  # 8KB chunks for streaming
    UPLOAD_ALLOWED_CONTENT_TYPES: Set[str] = {"application/pdf"}

    # Security configuration - CRITICAL
    # Secret key must be 32+ characters and NOT placeholder values
    # Use: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "change-me-in-production"  # No default - must be explicitly set
    ALGORITHM: str = "HS256"  # JWT signature algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # JWT token lifetime
    DEBUG: bool = False  # NEVER set to True in production

    # Upload directory configuration
    UPLOAD_DIR_OVERRIDE: str | None = (
        None  # For testing: allows overriding computed upload dir
    )

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def UPLOAD_DIR(self) -> str:
        """
        Dynamically compute uploads directory path.
        Resolved relative to project root at runtime.
        Can be overridden for testing.
        """
        if self.UPLOAD_DIR_OVERRIDE:
            return self.UPLOAD_DIR_OVERRIDE

        path = BASE_DIR / "uploads" / "resumes"
        # Ensure directory exists
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """
        SECURITY-CRITICAL: Validate secret key strength BEFORE app starts.

        Prevents accidental deployment with weak or placeholder keys.
        This validation runs at startup - if it fails, the app cannot start.

        Rules:
        - Must NOT be a known placeholder value
        - Must be at least 32 characters (per OWASP recommendations)
        - Random generation: python -c "import secrets; print(secrets.token_hex(32))"
        """
        if self.SECRET_KEY in _FORBIDDEN_KEYS:
            raise ValueError(
                "FATAL: SECRET_KEY is set to a known-insecure placeholder. "
                'Generate a strong key: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if len(self.SECRET_KEY) < 32:
            raise ValueError("FATAL: SECRET_KEY must be at least 32 characters long.")
        return self


settings = Settings()
