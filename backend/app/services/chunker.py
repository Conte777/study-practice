"""Fixed-window text chunking with overlap.

Splits text into 1000-character windows that overlap by 100 characters, so the
last 100 characters of chunk N are the first 100 characters of chunk N+1. This
keeps context across chunk boundaries for retrieval.
"""

CHUNK_SIZE = 1000
OVERLAP = 100


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Split ``text`` into overlapping fixed-size chunks.

    Args:
        text: Source text to split.
        chunk_size: Maximum characters per chunk (default 1000).
        overlap: Characters shared between consecutive chunks (default 100).

    Returns:
        Chunks in order. Text shorter than ``chunk_size`` returns a single
        chunk; empty/whitespace-only text returns ``[]``.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    step = chunk_size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        if start + chunk_size >= len(text):
            break
        start += step
    return chunks
