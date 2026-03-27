"""Service for indexing uploaded documents into the vector store."""

from __future__ import annotations

from sqlalchemy.orm import Session

from job_coach.app.core.logger import logger
from job_coach.app.models.resume import Resume
from job_coach.ml.embeddings import get_embedding_service, get_vector_store
from job_coach.ml.ingestion import chunk_text, extract_text_from_pdf


def index_resume(
    db: Session,
    resume_id: int,
    file_path: str,
    user_id: int,
) -> int:
    """Parse a resume PDF, chunk it, embed it, and store in Qdrant.

    Also stores the raw text in the Resume DB record.

    Args:
        db: Database session.
        resume_id: ID of the Resume record.
        file_path: Path to the saved PDF file.
        user_id: Owner user ID.

    Returns:
        Number of chunks indexed.
    """
    # 1. Extract text
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    raw_text = extract_text_from_pdf(pdf_bytes)

    # 2. Save raw text to DB
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if resume:
        resume.raw_text = raw_text
        db.commit()

    # 3. Chunk
    logger.debug("Chunking resume text for %s", resume_id)
    chunks = chunk_text(raw_text)
    if not chunks:
        logger.warning("No text extracted/chunked for resume %s", resume_id)
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

    logger.info(
        "Indexed %s chunks for resume %s (user %s)", len(chunks), resume_id, user_id
    )
    return len(chunks)
