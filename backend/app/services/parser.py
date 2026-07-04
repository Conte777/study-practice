"""Text extraction from PDF and DOCX files.

Produces a list of :class:`Page` records, one per source page (PDF) or one
logical page for DOCX. Extraction never raises on malformed input — a file
that cannot be parsed yields an empty page list.
"""

import logging
from dataclasses import dataclass

import pdfplumber
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Page:
    """A single extracted page.

    Attributes:
        page_number: 1-based page index within the source document.
        text: Plain text content of the page (may be empty).
    """

    page_number: int
    text: str


def extract_text(path: str, content_type: str) -> list[Page]:
    """Extract per-page text from a PDF or DOCX file.

    Args:
        path: Filesystem path to the saved upload.
        content_type: ``"pdf"`` or ``"docx"`` — selects the extractor.

    Returns:
        A list of non-empty :class:`Page` records. Empty or unparseable
        files return ``[]`` instead of raising.
    """
    try:
        if content_type == "pdf":
            return _extract_pdf(path)
        if content_type == "docx":
            return _extract_docx(path)
    except Exception:  # noqa: BLE001 — corrupt input must degrade, not crash the pipeline
        logger.exception("Text extraction failed for %s", path)
    return []


def _extract_pdf(path: str) -> list[Page]:
    pages: list[Page] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(Page(page_number=i, text=text))
    return pages


def _extract_docx(path: str) -> list[Page]:
    # ponytail: DOCX has no page concept in the XML — all paragraphs collapse to
    # page 1. Upgrade path: render to PDF (LibreOffice) if true page numbers matter.
    doc = DocxDocument(path)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
    return [Page(page_number=1, text=text)] if text else []
