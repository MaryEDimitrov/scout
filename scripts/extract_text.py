"""Developer-only: turn the shipped PDFs into plain .txt files.

Graders never need to run this. The extracted text is already in data/text/.

Usage:  python -I scripts/extract_text.py data/pdfs data/text
"""

import sys
from pathlib import Path

import pdfplumber


def extract(pdf_path: Path) -> str:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(f"=== Page {number} ===\n{text}")
    return "\n\n".join(pages) + "\n"


def main(pdf_root: Path, text_root: Path) -> None:
    for pdf_path in sorted(pdf_root.rglob("*.pdf")):
        out_path = text_root / pdf_path.relative_to(pdf_root).with_suffix(".txt")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        text = extract(pdf_path)
        out_path.write_text(text, encoding="utf-8")
        print(f"{len(text):>8} chars  {out_path}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
