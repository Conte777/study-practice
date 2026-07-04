"""QA-01 — upload validation matrix.

Upload validation is content-sniffed (magic bytes), not content-type-trusted:
the endpoint accepts real PDF/DOCX payloads and rejects empty, oversize, or
unrecognized content. These tests pin that validation behaviour — the negative
cases the ТЗ calls out (>20 MB, wrong format, empty file), the accepted formats,
and the size boundary.
"""

import io

import pytest

from app.services.uploads import MAX_SIZE_BYTES, sniff_type
from tests.conftest import make_docx

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _upload(client, name, data, content_type):
    return client.post(
        "/api/v1/documents/upload",
        files={"file": (name, io.BytesIO(data), content_type)},
    )


@pytest.mark.parametrize(
    ("name", "content_type", "data"),
    [
        ("ok.pdf", PDF, b"%PDF-1.4 real-enough payload"),
        ("ok.docx", DOCX, make_docx("real docx body")),
    ],
)
def test_accepts_supported_types(client, name, content_type, data):
    r = _upload(client, name, data, content_type)
    assert r.status_code == 200
    body = r.json()
    assert body["file_name"] == name
    assert body["status"] == "uploaded"
    assert set(body) == {"id", "file_name", "status", "uploaded_at"}


@pytest.mark.parametrize(
    ("name", "content_type"),
    [
        ("note.txt", "text/plain"),
        ("image.png", "image/png"),
        ("archive.zip", "application/zip"),
    ],
)
def test_rejects_unsupported_types(client, name, content_type):
    # Content is sniffed, so junk bytes are rejected regardless of the declared type.
    r = _upload(client, name, b"whatever", content_type)
    assert r.status_code == 400
    assert "detail" in r.json()


def test_rejects_empty_file(client):
    r = _upload(client, "empty.pdf", b"", PDF)
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


def test_rejects_oversize_file(client):
    # One byte over the limit — boundary of the size branch (checked before sniff).
    r = _upload(client, "big.pdf", b"\0" * (MAX_SIZE_BYTES + 1), PDF)
    assert r.status_code == 400
    assert "20 mb" in r.json()["detail"].lower()


def test_accepts_at_size_limit(client):
    # Exactly at the limit is allowed (boundary: > is rejected, == is not).
    data = b"%PDF-1.4" + b"\0" * (MAX_SIZE_BYTES - 8)
    r = _upload(client, "atlimit.pdf", data, PDF)
    assert r.status_code == 200


def test_upload_requires_file(client):
    # No multipart file part → 422 (FastAPI validation), never a 500.
    assert client.post("/api/v1/documents/upload").status_code == 422


def test_sniff_type_guards_accepted_content():
    # Guards the content contract from silent drift: PDF magic in, junk out.
    assert sniff_type("x", b"%PDF-1.4") == "pdf"
    assert sniff_type("x", b"whatever") is None
