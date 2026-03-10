from fastapi import APIRouter, Depends
from pydantic import BaseModel

from job_coach.app.api.dependencies import get_current_user
from job_coach.app.models.user import User

router = APIRouter(tags=["rag"])


class RAGQuery(BaseModel):
    query: str
    top_k: int = 5


class RAGResponse(BaseModel):
    query: str
    answer: str
    sources: list[str]


@router.post("/query", response_model=RAGResponse)
def rag_query(
    body: RAGQuery,
    current_user: User = Depends(get_current_user),
):
    """Query the RAG pipeline: embed → retrieve → LLM → structured response."""
    try:
        from job_coach.ml.rag import run_rag_pipeline

        result = run_rag_pipeline(
            query=body.query,
            user_id=current_user.id,
            top_k=body.top_k,
        )
        return RAGResponse(
            query=result.query,
            answer=result.answer,
            sources=result.sources,
        )
    except ImportError:
        return RAGResponse(
            query=body.query,
            answer=(
                "ML dependencies are not installed. Install with: pip install '.[ml]'"
            ),
            sources=[],
        )
