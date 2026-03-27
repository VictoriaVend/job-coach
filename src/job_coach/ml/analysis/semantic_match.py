"""Semantic Job Matching: calculate semantic
similarity between a resume and a job description."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from job_coach.app.core.config import settings
from job_coach.ml.embeddings.service import get_embedding_service


@dataclass
class SemanticMatchResult:
    """Result of semantic matching."""

    similarity_score: float
    interpretation: str


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(v1)
    b = np.array(v2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def generate_semantic_match(
    resume_text: str, job_description: str
) -> SemanticMatchResult:
    """Calculate the semantic similarity score between a resume and job description.

    This uses dense vector embeddings to capture the meaning of the texts beyond
    simple keyword matching.

    Args:
        resume_text: The full text of the resume.
        job_description: The full text of the job description.

    Returns:
        SemanticMatchResult with the score and a human-readable interpretation.
    """
    embedding_service = get_embedding_service()

    # Generate document-level embeddings
    # Note: For very long documents, chunking and averaging or using a specialized
    # document-level model is better, but this works well for standard lengths.
    try:
        from job_coach.ml.ingestion.parser import chunk_text

        # 1. Chunk texts safely (e.g. max 1000 chars per chunk to fit in 256
        # WordPieces safely)
        resume_chunks = chunk_text(
            resume_text,
            chunk_size=settings.SEMANTIC_MATCH_CHUNK_SIZE,
            chunk_overlap=settings.SEMANTIC_MATCH_CHUNK_OVERLAP,
        )
        job_chunks = chunk_text(
            job_description,
            chunk_size=settings.SEMANTIC_MATCH_CHUNK_SIZE,
            chunk_overlap=settings.SEMANTIC_MATCH_CHUNK_OVERLAP,
        )

        if not resume_chunks or not job_chunks:
            return SemanticMatchResult(
                similarity_score=0.0,
                interpretation="Empty document provided.",
            )

        # 2. Embed all chunks (Batching is much faster)
        resume_embs = embedding_service.embed_batch([c["text"] for c in resume_chunks])
        job_embs = embedding_service.embed_batch([c["text"] for c in job_chunks])

        # 3. Mean Pooling: Average the document chunks to get a global document
        # representation
        resume_mean = np.mean(resume_embs, axis=0).tolist()
        job_mean = np.mean(job_embs, axis=0).tolist()

        score = cosine_similarity(resume_mean, job_mean)

        # Convert to percentage
        match_percentage = round(max(0.0, score) * 100, 1)

        if match_percentage >= 80:
            interpretation = "Excellent match. Highly aligned semantically."
        elif match_percentage >= 65:
            interpretation = "Good match. Core concepts align well."
        elif match_percentage >= 50:
            interpretation = (
                "Moderate match. Some terminology differs or experience gaps exist."
            )
        else:
            interpretation = """Low match. The resume and
            job description describe conceptually different roles."""

        return SemanticMatchResult(
            similarity_score=match_percentage, interpretation=interpretation
        )
    except Exception as e:
        # Fallback or error handling
        return SemanticMatchResult(
            similarity_score=0.0,
            interpretation=f"""Could not calculate semantic
            match due to ML service error: {e}""",
        )
