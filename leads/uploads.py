"""Documents the journalist drags into the app (for example school board or town council minutes).

Uploads are combined with the shipped collection into a separate folder for that run, so the
shipped data is never changed. Uploaded text is untrusted like every other document.
"""

import hashlib
import html
import io
import json
import re
import shutil
import ssl
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import certifi
from pypdf import PdfReader

from . import config

MONTH_DATE = re.compile(r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                        r"\s+(\d{1,2}),\s+(\d{4})")
ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
UPLOAD_NOTE = ("\n- Documents in the 'uploads' folder were added by the journalist (for example school board or "
               "town council minutes). They may come from other public bodies than County Council.\n")


def safe_name(filename: str) -> str:
    """Keep letters, digits, dashes and underscores only, so a file name can't point anywhere else."""
    stem = Path(filename).stem
    return re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_")[:80] or "document"


def find_date(filename: str, text: str) -> str:
    if m := ISO_DATE.search(filename):
        return m.group(0)
    if m := MONTH_DATE.search(text[:3000]):
        return datetime.strptime(" ".join(m.groups()), "%B %d %Y").strftime("%Y-%m-%d")
    return ""


ROSTER_START = re.compile(r"window\.\w+\s*=\s*(?=\[)")
ROSTER_PAGE_SIZE = 20  # bookings per page, so each page stays small for the agents


def roster_pages(records: list[dict]) -> list[str]:
    """A saved Beaufort County inmate-inquiry page -> one line per booking.

    Only what a lead needs is kept. Home address, date of birth, race, sex, height, weight,
    photo link, and officer are dropped here, in code, before any AI sees the page.
    """
    lines = []
    for r in records:
        name = " ".join(x for x in (r.get("firstName"), r.get("middleName"), r.get("lastName"), r.get("suffix")) if x)
        released = f"{r.get('releaseDate', '')} {r.get('releaseTime', '')}".strip() or "not released"
        arrests = []
        for a in r.get("arrests", []):
            charges = "; ".join(f"{c.get('offense', '').strip()} ({c.get('statute', '').strip()}), bond "
                                f"${c.get('bond', '')}{', ' + c['court'] if c.get('court') else ''}"
                                for c in a.get("charges", []))
            arrests.append(f"Arresting agency: {a.get('agency', '')} | Charges: {charges}")
        lines.append(f"Booking {r.get('bookingNumber', '')} | Name: {name} | Booked: {r.get('bookingDate', '')} "
                     f"{r.get('bookingTime', '')} | Released: {released} | " + " | ".join(arrests))
    return ["\n".join(lines[i:i + ROSTER_PAGE_SIZE]) for i in range(0, len(lines), ROSTER_PAGE_SIZE)]


def roster_records(text: str) -> list[dict] | None:
    """Find the booking records the inmate-inquiry page embeds as data (each one has "arrests")."""
    for m in ROSTER_START.finditer(text):
        try:
            data, _ = json.JSONDecoder().raw_decode(text, m.end())
        except json.JSONDecodeError:
            continue
        if isinstance(data, list) and data and isinstance(data[0], dict) and "arrests" in data[0]:
            return data
    return None


def html_pages(text: str) -> tuple[list[str], str | None]:
    if records := roster_records(text):
        return roster_pages(records), None
    body = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    plain = html.unescape(re.sub(r"<[^>]+>", " ", body))
    plain = re.sub(r"[ \t]+", " ", re.sub(r"\s*\n\s*", "\n", plain)).strip()
    return ([plain], None) if plain else ([], "no readable text found in the web page.")


def extract_text(filename: str, data: bytes) -> tuple[list[str], str | None]:
    """Return (pages, warning). Plain text files become one page; saved web pages are converted."""
    if filename.lower().endswith((".html", ".htm")):
        pages, warning = html_pages(data.decode("utf-8", errors="replace"))
        return pages, f"{filename}: {warning}" if warning else None
    if filename.lower().endswith(".pdf"):
        try:
            pages = [page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages]
        except Exception:
            return [], f"{filename}: could not be read as a PDF."
        if not any(p.strip() for p in pages):
            return [], (f"{filename}: no text found. It may be a scanned image; "
                        "upload a PDF with selectable text or a .txt file.")
        return pages, None
    try:
        return [data.decode("utf-8")], None
    except UnicodeDecodeError:
        return [data.decode("latin-1")], None


class FetchFailed(Exception):
    """The jail roster could not be downloaded or read."""


def fetch_jail_roster(url: str = config.JAIL_ROSTER_URL, timeout: int = 20) -> tuple[str, bytes, int]:
    """Download the county's 72-hour booking roster. Returns (file name, page bytes, number of bookings)."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Lead Finder newsroom tool)"})
    # certifi's certificate bundle works on every computer, including Mac Python installs whose own
    # certificates were never set up (they fail every secure download otherwise).
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            data = response.read()
    except urllib.error.URLError as problem:
        if isinstance(problem.reason, ssl.SSLError):
            raise FetchFailed("The county site's secure connection could not be verified, so the jail roster was not "
                              "downloaded. Save the page from your browser and drag it in instead.")
        raise FetchFailed("Could not reach the county jail roster. Check your internet connection, or save the "
                          "page from your browser and drag it in instead.")
    except (TimeoutError, OSError):
        raise FetchFailed("Could not reach the county jail roster. Check your internet connection, or save the "
                          "page from your browser and drag it in instead.")
    records = roster_records(data.decode("utf-8", errors="replace"))
    if not records:
        raise FetchFailed("The jail roster page loaded, but no bookings could be read from it. The county may have "
                          "changed the page; save it from your browser and drag it in instead.")
    return f"jail_roster_{datetime.now():%Y-%m-%d_%H%M}.html", data, len(records)


def build_collection(files: list[tuple[str, bytes]], base_dir: Path = config.REAL_DATA_DIR,
                     uploads_root: Path = config.RUNS_DIR / "uploads",
                     sample_sets: list[str] | None = None) -> tuple[Path, list[dict]]:
    """Copy the shipped collection, any optional sets, and the uploads into one folder.

    Returns (text folder, file report).
    """
    sample_sets = sorted(sample_sets or [])
    digest = hashlib.sha256(b"".join(name.encode() + data for name, data in sorted(files))
                            + ",".join(sample_sets).encode()).hexdigest()[:12]
    text_dir = uploads_root / digest / "text"
    if text_dir.exists():
        shutil.rmtree(text_dir.parent)
    shutil.copytree(base_dir, text_dir)

    report = []
    for filename, data in files:
        pages, warning = extract_text(filename, data)
        if warning:
            report.append({"file": filename, "added": False, "note": warning})
            continue
        if filename.startswith("event_calendars_"):  # fetched for the Events beat, not uploaded
            target = text_dir / "events" / f"{safe_name(filename)}.txt"
            target.parent.mkdir(parents=True, exist_ok=True)
            text = data.decode("utf-8")  # already split into "=== Page N ===" sections
            target.write_text(text if "=== Page 1 ===" in text else "=== Page 1 ===\n" + text, encoding="utf-8")
            report.append({"file": filename, "added": True, "doc_id": target.stem, "pages": text.count("=== Page"),
                           "date": ""})
            continue
        date = find_date(filename, "\n".join(pages))
        doc_id = f"upload_{date + '_' if date and date not in safe_name(filename) else ''}{safe_name(filename)}"
        target = text_dir / "uploads" / f"{doc_id}.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n\n".join(f"=== Page {i} ===\n{p.strip()}" for i, p in enumerate(pages, 1)) + "\n",
                          encoding="utf-8")
        original = text_dir.parent / "pdfs" / "uploads" / f"{doc_id}{Path(filename).suffix.lower()}"
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(data)
        report.append({"file": filename, "added": True, "doc_id": doc_id, "pages": len(pages),
                       "date": date or "unknown"})

    added_notes = UPLOAD_NOTE if files else ""
    for name in sample_sets:
        shutil.copytree(config.SAMPLES_DIR / name / "text", text_dir / name)
        info = config.SAMPLE_SETS[name]
        added_notes += f"\n- Folder '{name}': {info['label']} ({info['dates']}), added by the journalist.\n"

    notes = text_dir / "COLLECTION_NOTES.md"
    notes.write_text((notes.read_text() if notes.exists() else "") + added_notes)
    return text_dir, report
