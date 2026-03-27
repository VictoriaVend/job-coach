from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from job_coach.app.api.dependencies import get_current_user
from job_coach.app.core.config import settings
from job_coach.app.core.logger import logger
from job_coach.app.models.user import User

router = APIRouter(tags=["rag"])


class RAGQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=settings.RAG_QUERY_MAX_CHARS)
    top_k: int = Field(
        settings.RAG_TOP_K_DEFAULT,
        ge=settings.RAG_TOP_K_MIN,
        le=settings.RAG_TOP_K_MAX,
    )


class RAGSource(BaseModel):
    text: str
    score: float
    document_id: int | None = None
    document_type: str
    chunk_index: int | None = None


class RAGResponse(BaseModel):
    query: str
    answer: str
    sources: list[RAGSource]


@router.post("/query", response_model=RAGResponse)
async def rag_query(
    body: RAGQuery,
    current_user: User = Depends(get_current_user),
):
    """Query the RAG pipeline: embed → retrieve → LLM → structured response."""
    logger.info(
        f"User {current_user.id} querying RAG pipeline: "
        f"'{body.query}' (top_k={body.top_k})"
    )
    try:
        from job_coach.ml.rag import run_rag_pipeline
        from job_coach.ml.rag.pipeline import (
            RAGConfigurationError,
            RAGDependencyError,
            RAGExecutionError,
        )

        result = await run_rag_pipeline(
            query=body.query,
            user_id=current_user.id,
            top_k=body.top_k,
        )
        return RAGResponse(
            query=result.query,
            answer=result.answer,
            sources=result.sources,
        )
    except RAGDependencyError as e:
        logger.error(f"RAG pipeline error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML dependencies are not installed. Run: pip install '.[ml]'",
        )
    except RAGConfigurationError as e:
        logger.warning(f"RAG pipeline misconfigured for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except RAGExecutionError as e:
        logger.error(f"RAG pipeline runtime error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
