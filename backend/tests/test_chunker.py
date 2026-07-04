from app.services.chunker import CHUNK_SIZE, OVERLAP, chunk_text


def test_empty_or_whitespace():
    assert chunk_text("") == []
    assert chunk_text("   \n\t ") == []


def test_short_text_single_chunk():
    assert chunk_text("hello world") == ["hello world"]


def test_size_and_overlap_invariant():
    text = "".join(chr(ord("a") + i % 26) for i in range(2600))
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= CHUNK_SIZE for c in chunks)
    for a, b in zip(chunks, chunks[1:], strict=False):
        assert a[-OVERLAP:] == b[:OVERLAP]  # last 100 of N == first 100 of N+1


def test_exact_chunk_size():
    assert chunk_text("x" * CHUNK_SIZE) == ["x" * CHUNK_SIZE]
