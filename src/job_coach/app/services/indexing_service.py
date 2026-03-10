"""Service for indexing uploaded documents into the vector store."""

from __future__ import annotations

from sqlalchemy.orm import Session

from job_coach.app.models.resume import Resume
from job_coach.ml.embeddings import get_embedding_service, get_vector_store
from job_coach.ml.ingestion import chunk_text, extract_text_from_pdf


def index_resume(
    db: Session,
    resume_id: int,
    pdf_bytes: bytes,
    user_id: int,
) -> int:
    """Parse a resume PDF, chunk it, embed it, and store in Qdrant.

    Also stores the raw text in the Resume DB record.

    Args:
        db: Database session.
        resume_id: ID of the Resume record.
        pdf_bytes: Raw PDF file bytes.
        user_id: Owner user ID.

    Returns:
        Number of chunks indexed.
    """
    # 1. Extract text
    raw_text = extract_text_from_pdf(pdf_bytes)

    # 2. Save raw text to DB
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if resume:
        resume.raw_text = raw_text
        db.commit()

    # 3. Chunk
    chunks = chunk_text(raw_text)
    if not chunks:
        return 0

    # 4. Embed
    embedding_service = get_embedding_service()
    texts = [c["text"] for c in chunks]
    embeddings = embedding_service.embed_batch(texts)

    # 5. Store in Qdrant
    vector_store = get_vector_store()
    vector_store.ensure_collection(vector_size=embedding_service.dimension)
    vector_store.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
        user_id=user_id,
        document_id=resume_id,
        document_type="resume",
    )

    return len(chunks)
