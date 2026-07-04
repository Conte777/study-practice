from app.services.parser import extract_text
from tests.conftest import make_docx


def test_docx_extraction(tmp_path):
    p = tmp_path / "d.docx"
    p.write_bytes(make_docx("Привет мир\nвторая строка"))
    pages = extract_text(str(p), "docx")
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Привет" in pages[0].text
    assert "вторая" in pages[0].text


def test_corrupt_pdf_degrades(tmp_path):
    p = tmp_path / "bad.pdf"
    p.write_bytes(b"%PDF-1.4 not actually a pdf")
    assert extract_text(str(p), "pdf") == []  # no crash


def test_empty_docx(tmp_path):
    p = tmp_path / "empty.docx"
    p.write_bytes(make_docx(""))
    assert extract_text(str(p), "docx") == []


def test_unknown_type():
    assert extract_text("nonexistent", "txt") == []
