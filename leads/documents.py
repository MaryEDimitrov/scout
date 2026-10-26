"""Loads the document collection from text files and finds things in it."""

import re
from dataclasses import dataclass
from pathlib import Path

DOC_TYPES = {
    "trackers": "Capital project tracker (dated snapshot)",
    "council": "Council or committee agenda/minutes",
    "packet_excerpts": "Meeting backup packet (excerpt)",
    "uploads": "Uploaded by the journalist",
    "hilton_head": "Hilton Head Island Town Council minutes",
    "county_recent": "Beaufort County Council or committee minutes (recent)",
    "events": "Local event calendars (fetched today)",
    "school_board": "Beaufort County School District board agenda",
}
# Folders whose documents a journalist added for this search (uploads and one-click sets)
ADDED_FOLDERS = {"uploads", "hilton_head", "school_board", "county_recent", "events"}
SHIPPED_PDFS = Path(__file__).resolve().parent.parent / "data" / "pdfs"
SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples"
PAGE_MARKER = re.compile(r"^=== Page (\d+) ===$", re.MULTILINE)
DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
DOLLARS = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?")


@dataclass
class Document:
    doc_id: str  # file name without extension, e.g. "tracker_2021-05-10"
    doc_type: str
    date: str
    pages: list[str]
    source_file: str  # the file a journalist would open, e.g. "tracker_2021-05-10.pdf"
    added: bool = False  # True if the journalist added it for this search

    @property
    def full_text(self) -> str:
        return "\n".join(self.pages)


class DocumentStore:
    """All documents in one folder (real data or test fixtures)."""

    def __init__(self, text_dir: Path):
        self.text_dir = Path(text_dir)
        self.docs: dict[str, Document] = {}
        for path in sorted(self.text_dir.rglob("*.txt")):
            self.docs[path.stem] = self._load(path)
        notes = self.text_dir / "COLLECTION_NOTES.md"
        self.notes = notes.read_text(encoding="utf-8").strip() if notes.exists() else ""

    def _load(self, path: Path) -> Document:
        text = path.read_text(encoding="utf-8")
        pages = [p.strip() for p in PAGE_MARKER.split(text)[2::2]] or [text.strip()]
        relative = path.relative_to(self.text_dir).with_suffix(".pdf")
        originals = [self.text_dir.parent / "pdfs" / relative, SHIPPED_PDFS / relative,
                     SAMPLES / relative.parts[0] / "pdfs" / relative.name]
        date = DATE.search(path.stem)
        return Document(
            doc_id=path.stem,
            doc_type=DOC_TYPES.get(path.parent.name, path.parent.name),
            date=date.group(1) if date else "",
            pages=pages,
            source_file=relative.name if any(p.exists() for p in originals) else path.name,
            added=path.parent.name in ADDED_FOLDERS,
        )

    def get(self, doc_id: str) -> Document | None:
        return self.docs.get(doc_id.removesuffix(".pdf").removesuffix(".txt"))


def name_pattern(name: str) -> re.Pattern:
    """A forgiving pattern for a project name or keyword.

    Ignores case and punctuation between words, and treats "Ft." and "Fort"
    as the same word, so "Fort Fremont" finds "Ft. Fremont".
    """
    words = re.findall(r"[A-Za-z0-9#]+", name)
    parts = [r"(?:fort|ft)" if w.lower() in ("fort", "ft") else re.escape(w) for w in words]
    return re.compile(r"\b" + r"\W+".join(parts) + r"\b", re.IGNORECASE)


def dollar_amounts(text: str) -> list[str]:
    return DOLLARS.findall(text)


def dollars_to_number(amount: str) -> float:
    return float(amount.replace("$", "").replace(",", "").strip())
