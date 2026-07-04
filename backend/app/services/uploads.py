"""Upload validation: content-sniffed file type and size-capped streaming to disk."""

import os
import tempfile
import zipfile

from fastapi import UploadFile

MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB limit
_READ_CHUNK = 1 << 20  # 1 MiB streaming reads


class InvalidUploadError(Exception):
    """Raised when an upload fails content/size validation; callers map it to HTTP 400."""


def unlink(path: str) -> None:
    """Remove a file if it exists; a no-op otherwise."""
    if os.path.exists(path):
        os.unlink(path)


def sniff_type(path: str, header: bytes) -> str | None:
    """Detect the file type from content, not extension.

    Args:
        path: Path to the saved upload (needed to inspect DOCX zip entries).
        header: The first bytes of the file.

    Returns:
        ``"pdf"``, ``"docx"``, or ``None`` if the content matches neither.
    """
    if header.startswith(b"%PDF"):
        return "pdf"
    if header.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as zf:
                if any(name.startswith("word/") for name in zf.namelist()):
                    return "docx"
        except zipfile.BadZipFile:
            return None
    return None


async def save_upload(file: UploadFile) -> tuple[str, str]:
    """Stream an upload to a temp file, enforcing the size cap and content type.

    Reads in bounded chunks so a huge upload never lands fully in memory; aborts
    as soon as the cumulative size exceeds the limit.

    Returns:
        A ``(temp_path, file_type)`` tuple.

    Raises:
        InvalidUploadError: For empty files, oversize uploads, or unsupported
            content. Callers map this to an HTTP 400.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115 — outlives this scope
    header = b""
    total = 0
    try:
        while chunk := await file.read(_READ_CHUNK):
            total += len(chunk)
            if total > MAX_SIZE_BYTES:
                raise InvalidUploadError("File exceeds 20 MB limit")
            if not header:
                header = chunk[:8]
            tmp.write(chunk)
        tmp.close()
        if total == 0:
            raise InvalidUploadError("Empty file")
        file_type = sniff_type(tmp.name, header)
        if file_type is None:
            raise InvalidUploadError("Unsupported file type (expected PDF or DOCX)")
        return tmp.name, file_type
    except Exception:
        tmp.close()
        unlink(tmp.name)
        raise
