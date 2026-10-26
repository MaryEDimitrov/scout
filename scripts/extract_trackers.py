"""Developer-only: turn the capital project tracker PDFs into one-row-per-line text.

The trackers are tables. Plain text extraction mixes the columns together
(a project name ends up split across lines with other columns in between),
which breaks keyword search and verbatim quote checks. This script rebuilds
each table row from word positions instead:

  - row boundaries come from the thin horizontal rules drawn between rows
  - column boundaries come from the empty vertical gaps between columns,
    measured over all rows of a table section

Every word in the output is copied from the PDF; only the layout changes.

Usage:  python -I scripts/extract_trackers.py data/pdfs/trackers data/text/trackers
"""

import re
import sys
from pathlib import Path

import pdfplumber

FULL_COLUMNS = ["Project Name", "Description", "Project Cost", "Funding Source", "Project Status"]
SHORT_COLUMNS = ["Project Name", "Description", "Project Status"]  # "In Development" tables
SECTION = re.compile(r"^(CONSTRUCTION|DESIGN|IN DEVELOPMENT)\b")
GAPS = (6, 4, 2, 1)  # points of empty space that separate two columns; tried largest first


def join_words(words):
    """Join words in reading order: top to bottom, then left to right."""
    lines = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if lines and abs(lines[-1][-1]["top"] - w["top"]) < 3:
            lines[-1].append(w)
        else:
            lines.append([w])
    return " ".join(" ".join(x["text"] for x in sorted(line, key=lambda w: w["x0"])) for line in lines)


def column_spans(rows, min_gap):
    """Find columns as the x-ranges covered by words, split wherever all rows leave a gap."""
    spans = sorted((w["x0"], w["x1"]) for row in rows for w in row)
    columns = []
    for x0, x1 in spans:
        if columns and x0 <= columns[-1][1] + min_gap:
            columns[-1][1] = max(columns[-1][1], x1)
        else:
            columns.append([x0, x1])
    return columns


def table_lines(rows, labels):
    """Format each table row as 'Label: text | Label: text | ...'."""
    columns = next((c for gap in GAPS if len(c := column_spans(rows, gap)) == len(labels)), None)
    if columns is None:  # layout not understood: keep the rows as plain text
        return [join_words(row) for row in rows]
    lines = []
    for row in rows:
        cells = [[w for w in row if c[0] <= w["x0"] and w["x1"] <= c[1]] for c in columns]
        lines.append(" | ".join(f"{label}: {join_words(cell)}" for label, cell in zip(labels, cells) if cell))
    return lines


def page_rows(page):
    words = page.extract_words()
    separators = sorted({r["top"] for r in page.rects if r["height"] < 2 and r["width"] > 100})
    out = [join_words([w for w in words if separators and w["bottom"] <= separators[0]])]  # page title
    rows, labels = [], None
    for top, bottom in zip(separators, separators[1:]):
        band = [w for w in words if top <= (w["top"] + w["bottom"]) / 2 < bottom]
        if not band:
            continue
        text = join_words(band)
        if any(w["text"] == "Description" for w in band):  # header row starts a new table
            labels = FULL_COLUMNS if any(w["text"] == "Cost" for w in band) else SHORT_COLUMNS
        elif SECTION.match(text):  # green section bar, e.g. "CONSTRUCTION Updated May 10, 2021"
            if rows:
                out += table_lines(rows, labels)
            rows = []
            out.append(f"## {text}")
        elif labels:
            rows.append(band)
        else:
            out.append(text)
    if rows:
        out += table_lines(rows, labels)
    return out


def main(pdf_dir: Path, text_dir: Path) -> None:
    text_dir.mkdir(parents=True, exist_ok=True)
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for number, page in enumerate(pdf.pages, start=1):
                pages.append(f"=== Page {number} ===\n" + "\n".join(page_rows(page)))
        text = re.sub(r"[ \t]+", " ", "\n\n".join(pages)) + "\n"
        out_path = text_dir / (pdf_path.stem + ".txt")
        out_path.write_text(text, encoding="utf-8")
        print(f"{len(text):>8} chars  {out_path}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
