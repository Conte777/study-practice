# Test fixtures — name manifest (contract QA ↔ BE)

Binaries are added by the QA stage-1 (the ТЗ permits committing them **only** here).
These names are already hard-wired into the BE upload gates — treat them as a contract.

| File | Purpose | Expected upload result |
|---|---|---|
| `ok.pdf` | valid PDF | 200 |
| `ok.docx` | valid DOCX | 200 |
| `empty.pdf` | zero-content PDF | 400 (empty) |
| `empty.docx` | zero-content DOCX | 400 (empty) |
| `corrupt.pdf` | broken PDF bytes | 400 / error status |
| `fonts.pdf` | PDF with embedded/exotic fonts | 200 (extraction edge case) |
| `big.bin` | > 20 МБ | 400 (size limit) |
| `note.txt` | unsupported type | 400 (content-type) |
