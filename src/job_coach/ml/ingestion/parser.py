"""Document ingestion pipeline: PDF parsing and text chunking."""

from __future__ import annotations

import re


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
    chunk_size: int = 500,
    chunk_overlap: int = 50,
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

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look back for sentence-ending punctuation
            for boundary in (". ", "! ", "? ", "\n"):
                last_boundary = text.rfind(boundary, start + chunk_size // 2, end)
                if last_boundary != -1:
                    end = last_boundary + len(boundary)
                    break

        chunk_text_segment = text[start:end].strip()
        if chunk_text_segment:
            chunks.append(
                {
                    "text": chunk_text_segment,
                    "chunk_index": chunk_index,
                    "start_char": start,
                    "end_char": end,
                }
            )
            chunk_index += 1

        start = end - chunk_overlap
        if start >= len(text):
            break
        # Avoid infinite loop
        if end >= len(text):
            break

    return chunks
