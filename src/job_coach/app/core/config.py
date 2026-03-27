from pathlib import Path

from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings

_FORBIDDEN_KEYS = {"change-me-in-production", "your_secret_key_here", "", "secret"}


class Settings(BaseSettings):
    APP_NAME: str = "AI-powered Job Coach"
    APP_VERSION: str = "0.1.0"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/job_coach"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"
    CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    HUGGINGFACEHUB_API_TOKEN: str | None = None
    HF_MODEL_ID: str = "mistralai/Mistral-7B-Instruct-v0.3"
    EMBEDDING_MODEL_ID: str = "all-MiniLM-L6-v2"
    RAG_LLM_TASK: str = "text-generation"
    RAG_LLM_TEMPERATURE: float = 0.1
    RAG_LLM_MAX_NEW_TOKENS: int = 512
    RAG_LLM_DO_SAMPLE: bool = True
    RAG_TOP_K_DEFAULT: int = 5
    RAG_TOP_K_MIN: int = 1
    RAG_TOP_K_MAX: int = 20
    RAG_QUERY_MAX_CHARS: int = 2000
    ANALYSIS_TEXT_MAX_CHARS: int = 50_000

    INGEST_CHUNK_SIZE: int = 500
    INGEST_CHUNK_OVERLAP: int = 50
    SEMANTIC_MATCH_CHUNK_SIZE: int = 1000
    SEMANTIC_MATCH_CHUNK_OVERLAP: int = 100

    # No default - must be explicitly set in .env
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def UPLOAD_DIR(self) -> str:
        return str(Path(__file__).resolve().parents[4] / "uploads" / "resumes")

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """Reject weak/placeholder secret keys unconditionally (not just in prod)."""
        if self.SECRET_KEY in _FORBIDDEN_KEYS:
            raise ValueError(
                "FATAL: SECRET_KEY is set to a known-insecure placeholder. "
                'Generate a strong key: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if len(self.SECRET_KEY) < 32:
            raise ValueError("FATAL: SECRET_KEY must be at least 32 characters long.")
        return self


settings = Settings()
