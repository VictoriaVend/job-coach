"""Document ingestion pipeline: PDF parsing and text chunking."""

from __future__ import annotations

import re

from job_coach.app.core.config import settings


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract raw text from a PDF file using PyMuPDF (fitz).

    Args:
        pdf_bytes: Raw bytes of the PDF file.

    Returns:
        Extracted plain text from all pages.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF parsing. Install it with: pip install PyMuPDF"
        ) from exc

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages)


def chunk_text(
    text: str,
    chunk_size: int = settings.INGEST_CHUNK_SIZE,
    chunk_overlap: int = settings.INGEST_CHUNK_OVERLAP,
) -> list[dict]:
    """Split text into overlapping chunks for embedding.

    Uses a simple character-based sliding window approach.
    Each chunk includes metadata about its position.

    Args:
        text: Input text to chunk.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of dicts with keys: 'text', 'chunk_index', 'start_char', 'end_char'.
    """
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as e:
        raise ImportError(
            "langchain is required for optimal text chunking. Install with: pip install langchain"
        ) from e

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        add_start_index=True,
    )

    docs = splitter.create_documents([text])
    chunks = []

    for i, doc in enumerate(docs):
        start_char = doc.metadata.get("start_index", 0)
        chunk_text_segment = doc.page_content.strip()
        end_char = start_char + len(chunk_text_segment)

        chunks.append(
            {
                "text": chunk_text_segment,
                "chunk_index": i,
                "start_char": start_char,
                "end_char": end_char,
            }
        )

    return chunks
