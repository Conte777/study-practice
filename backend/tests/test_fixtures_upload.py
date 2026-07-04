"""QA-03 fixtures driven through the QA-01 upload validation.

Skips if fixtures haven't been generated (they're git-ignored — run
`uv run --with reportlab --with python-docx python tests/fixtures/generate.py`).

Upload validation is synchronous (content-type sniff, size, empty-bytes);
parsing runs in a background task, so a file that *sniffs* as a valid PDF/DOCX
but is internally broken still returns 200 (it fails async, status→error).
Those cases (empty.docx / corrupt.pdf) stay xfail — the sync 400 can't see them.
corrupt.docx is different: its broken zip fails the sniff, so it's rejected 400.
"""

import mimetypes
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"

pytestmark = pytest.mark.skipif(
    not (FIXTURES / "ok.pdf").exists(),
    reason="fixtures not generated (see tests/fixtures/generate.py)",
)

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _content_type(name: str) -> str:
    if name.endswith(".docx"):
        return DOCX
    guessed, _ = mimetypes.guess_type(name)
    return guessed or "application/octet-stream"


def _upload(client, name: str):
    data = (FIXTURES / name).read_bytes()
    return client.post(
        "/api/v1/documents/upload",
        files={"file": (name, data, _content_type(name))},
    )


@pytest.mark.parametrize("name", ["ok.pdf", "ok.docx", "fonts.pdf"])
def test_valid_fixtures_accepted(client, name):
    assert _upload(client, name).status_code == 200


@pytest.mark.parametrize(
    "name",
    ["empty.pdf", "note.txt", "big.bin", "corrupt.docx"],
)
def test_invalid_fixtures_rejected(client, name):
    # empty.pdf → empty-bytes branch; note.txt & big.bin → content-type branch
    # (big.bin guesses to application/octet-stream, rejected before the size check;
    # the >20 MB size boundary itself is covered in test_upload_validation.py).
    # corrupt.docx → PK header but a broken zip, so the content sniff rejects it.
    assert _upload(client, name).status_code == 400


@pytest.mark.parametrize("name", ["empty.docx", "corrupt.pdf"])
@pytest.mark.xfail(
    reason="sniffs as valid PDF/DOCX; only background parsing rejects it, so upload returns 200",
    strict=True,
)
def test_parser_branch_fixtures_rejected(client, name):
    assert _upload(client, name).status_code == 400
