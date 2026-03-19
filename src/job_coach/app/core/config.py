from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/job_coach"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"
    HUGGINGFACEHUB_API_TOKEN: str | None = None
    HF_MODEL_ID: str = "mistralai/Mistral-7B-Instruct-v0.3"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
