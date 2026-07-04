"""QA-01 — upload validation matrix.

The current upload endpoint is a mock: it validates content-type, empty-bytes
and the 20 MB size limit, but does not parse/index (BE stages 2/3). These tests
pin the *validation behaviour* — the negative cases the ТЗ calls out
(>20 MB, wrong format, empty file) plus the accepted formats.
"""

import io

import pytest

from app.api.documents import ALLOWED_CONTENT_TYPES, MAX_SIZE_BYTES

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _upload(client, name, data, content_type):
    return client.post(
        "/api/v1/documents/upload",
        files={"file": (name, io.BytesIO(data), content_type)},
    )


@pytest.mark.parametrize(
    ("name", "content_type"),
    [("ok.pdf", PDF), ("ok.docx", DOCX)],
)
def test_accepts_supported_types(client, name, content_type):
    r = _upload(client, name, b"%PDF-1.4 real-enough payload", content_type)
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
    r = _upload(client, name, b"whatever", content_type)
    assert r.status_code == 400
    assert "detail" in r.json()


def test_rejects_empty_file(client):
    r = _upload(client, "empty.pdf", b"", PDF)
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


def test_rejects_oversize_file(client):
    # One byte over the limit — boundary of the size branch.
    r = _upload(client, "big.pdf", b"\0" * (MAX_SIZE_BYTES + 1), PDF)
    assert r.status_code == 400
    assert "20 mb" in r.json()["detail"].lower()


def test_accepts_at_size_limit(client):
    # Exactly at the limit is allowed (boundary: > is rejected, == is not).
    r = _upload(client, "atlimit.pdf", b"\0" * MAX_SIZE_BYTES, PDF)
    assert r.status_code == 200


def test_upload_requires_file(client):
    # No multipart file part → 422 (FastAPI validation), never a 500.
    assert client.post("/api/v1/documents/upload").status_code == 422


def test_allowed_types_are_pdf_and_docx():
    # Guards the content-type contract from silent drift.
    assert {PDF, DOCX} == ALLOWED_CONTENT_TYPES
