"""RAG pipeline: retrieval-augmented generation using Qdrant + Ollama."""

from __future__ import annotations

from dataclasses import dataclass, field

from job_coach.app.core.config import settings
from job_coach.ml.embeddings import get_embedding_service, get_vector_store


@dataclass
class RAGResult:
    """Structured result from the RAG pipeline."""

    query: str
    answer: str
    sources: list[dict] = field(default_factory=list)


def build_context(retrieved_chunks: list[dict]) -> str:
    """Build a context string from retrieved chunks for LLM prompt.

    Args:
        retrieved_chunks: Results from vector store search.

    Returns:
        Formatted context string.
    """
    if not retrieved_chunks:
        return "No relevant documents found."

    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        score = chunk.get("score", 0)
        text = chunk.get("text", "")
        doc_type = chunk.get("document_type", "unknown")
        context_parts.append(
            f"[Source {i} ({doc_type}, relevance: {score:.2f})]\n{text}"
        )

    return "\n\n".join(context_parts)


def query_ollama(query: str, context: str) -> str:
    """Send a prompt to Ollama using LangChain and return the response.

    Args:
        query: User's question.
        context: Retrieved context from vector search.

    Returns:
        LLM response text.
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain_community.llms import Ollama
    except ImportError as exc:
        raise ImportError(
            "langchain and langchain-community are required. "
            "Install with: pip install langchain langchain-community"
        ) from exc

    import httpx

    # Check if Ollama is accessible first
    try:
        httpx.get(f"{settings.OLLAMA_URL}/api/version", timeout=2.0)
    except Exception:
        return (
            "Ollama service is not available. "
            "Please ensure Ollama is running at " + settings.OLLAMA_URL
        )

    # Define LangChain prompt
    template = """You are an AI Job Coach assistant. Use the provided context to answer 
the user's question. If the context doesn't contain relevant information, say so 
honestly. Always be helpful and provide actionable advice.

Context:
{context}

Question: {query}

Answer in a structured, professional manner. Focus on actionable insights."""

    prompt = PromptTemplate.from_template(template)

    # Initialize LangChain Ollama wrapper
    llm = Ollama(
        model="llama3.2",
        base_url=settings.OLLAMA_URL,
        temperature=0.3,  # low temp for more factual retrieval answers
    )

    # Create and run the chain
    chain = prompt | llm

    try:
        return chain.invoke({"context": context, "query": query})
    except Exception as e:
        return f"Error querying LLM via LangChain: {e!s}"


def run_rag_pipeline(
    query: str,
    user_id: int,
    top_k: int = 5,
) -> RAGResult:
    """Execute the full RAG pipeline.

    Flow:
    1. Embed the query using sentence-transformers
    2. Retrieve relevant chunks from Qdrant (filtered by user)
    3. Build context from retrieved chunks
    4. Send context + query to Ollama LLM
    5. Return structured response

    Args:
        query: User's question.
        user_id: Current user's ID for scoping search.
        top_k: Number of chunks to retrieve.

    Returns:
        RAGResult with answer and source documents.
    """
    # 1. Embed query
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.embed_text(query)

    # 2. Retrieve from Qdrant
    vector_store = get_vector_store()
    retrieved_chunks = vector_store.search(
        query_embedding=query_embedding,
        user_id=user_id,
        top_k=top_k,
    )

    # 3. Build context
    context = build_context(retrieved_chunks)

    # 4. Query LLM via LangChain
    answer = query_ollama(query, context)

    # 5. Return structured result
    sources = [
        {
            "text": chunk["text"][:200] + "..."
            if len(chunk["text"]) > 200
            else chunk["text"],
            "score": chunk.get("score", 0.0),
            "document_type": chunk.get("document_type", "unknown"),
        }
        for chunk in retrieved_chunks
    ]

    return RAGResult(
        query=query,
        answer=answer,
        sources=[s["text"] for s in sources],
    )
