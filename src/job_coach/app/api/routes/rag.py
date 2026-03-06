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
    """Query the RAG pipeline.

    TODO: Wire up to ml/rag/ pipeline:
    1. Embed query via sentence-transformers
    2. Vector search in Qdrant
    3. Build context from retrieved chunks
    4. Send to Ollama LLM
    5. Return structured response
    """
    return RAGResponse(
        query=body.query,
        answer="RAG pipeline is not yet connected. This is a placeholder response.",
        sources=[],
    )
