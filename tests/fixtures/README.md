# Test fixtures — name manifest (contract QA ↔ BE)

Binaries are **git-ignored** — generate them on demand; `generate.py` is the
source of truth (creates all names in the table below plus the QA-05 golden set):

```bash
uv run --with reportlab --with python-docx python tests/fixtures/generate.py
```

These names are hard-wired into the BE upload gates — treat them as a contract.

| File | Purpose | Expected upload result |
|---|---|---|
| `ok.pdf` | valid PDF | 200 |
| `ok.docx` | valid DOCX | 200 |
| `empty.pdf` | zero-content PDF | 400 (empty) |
| `empty.docx` | zero-content DOCX | 400 (empty) |
| `corrupt.pdf` | broken PDF bytes | 400 / error status |
| `corrupt.docx` | broken DOCX (invalid zip) | 400 / error status |
| `fonts.pdf` | PDF with embedded/exotic fonts | 200 (extraction edge case) |
| `big.bin` | > 20 МБ | 400 (size limit) |
| `note.txt` | unsupported type | 400 (content-type) |
