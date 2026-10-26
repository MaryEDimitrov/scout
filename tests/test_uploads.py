"""Journalist uploads: minutes dragged into the app join the collection safely."""

from leads import config, tools
from leads.documents import DocumentStore
from leads.uploads import build_collection, safe_name

MINUTES = b"""TOWN OF HILTON HEAD ISLAND - TOWN COUNCIL MINUTES - March 7, 2023
The Council approved a contract for beach renourishment in the amount of $4,250,000."""


def test_uploaded_minutes_join_the_real_collection(tmp_path):
    text_dir, report = build_collection([("HHI council minutes.txt", MINUTES)], uploads_root=tmp_path)
    store = DocumentStore(text_dir)
    assert len(store.docs) == len(DocumentStore(config.CURRENT_DATA_DIR).docs) + 1
    doc = store.get(report[0]["doc_id"])
    assert doc.doc_type == "Uploaded by the journalist"
    assert doc.date == "2023-03-07"  # found in the text
    assert "added by the journalist" in store.notes.lower()


def test_quotes_from_uploads_can_be_found_and_verified(tmp_path):
    text_dir, report = build_collection([("hhi.txt", MINUTES)], uploads_root=tmp_path)
    store = DocumentStore(text_dir)
    result = tools.fetch_passage(store, report[0]["doc_id"], "beach renourishment in the amount of $4,250,000")
    assert result["found"]


def test_real_pdf_upload_is_read(tmp_path):
    pdf = (config.PROJECT_DIR / "data" / "pdfs" / "council" / "2022-02-07_exec_minutes_293.pdf").read_bytes()
    text_dir, report = build_collection([("exec minutes.pdf", pdf)], uploads_root=tmp_path)
    assert report[0]["added"] and report[0]["pages"] >= 3
    store = DocumentStore(text_dir)
    assert store.get(report[0]["doc_id"]).source_file.endswith(".pdf")
    assert tools.search_documents(store, "Change Order 2")["total_matches"] > 0


def test_shipped_documents_still_point_to_their_pdfs(tmp_path):
    text_dir, _ = build_collection([("hhi.txt", MINUTES)], uploads_root=tmp_path)
    assert DocumentStore(text_dir).get("2026-01-12_council_minutes_1544").source_file == "2026-01-12_council_minutes_1544.pdf"


def test_pdf_without_text_gets_a_plain_warning(tmp_path):
    _, report = build_collection([("scan.pdf", b"%PDF-1.4 not really a pdf")], uploads_root=tmp_path)
    assert report[0]["added"] is False and "PDF" in report[0]["note"]


def test_file_names_cannot_escape_the_upload_folder():
    assert safe_name("../../etc/passwd.txt") == "passwd"
    assert "/" not in safe_name("a/b\\c..d.pdf")


def test_shipped_data_is_never_changed(tmp_path):
    before = sorted(p.name for p in config.CURRENT_DATA_DIR.rglob("*"))
    build_collection([("hhi.txt", MINUTES)], uploads_root=tmp_path)
    assert sorted(p.name for p in config.CURRENT_DATA_DIR.rglob("*")) == before


ROSTER = config.PROJECT_DIR / "test_fixtures" / "uploads" / "sample_jail_roster.html"


def test_saved_jail_roster_becomes_one_line_per_booking_with_charges():
    from leads.uploads import extract_text
    pages, warning = extract_text(ROSTER.name, ROSTER.read_bytes())
    text = "\n".join(pages)
    assert warning is None and text.count("Booking ") == 3
    assert "Name: PETER VOSS" in text and "BREACH OF TRUST WITH FRAUDULENT INTENT" in text


def test_jail_roster_drops_address_birth_date_race_and_body_details():
    from leads.uploads import extract_text
    text = "\n".join(extract_text(ROSTER.name, ROSTER.read_bytes())[0])
    for private in ["12 HERON WAY", "01/02/1971", "29900", "W/M", "5'10", "181", "example.invalid", "Officer, A"]:
        assert private not in text


def test_check_the_jail_log_reads_the_fetched_page(monkeypatch):
    import io
    from leads import uploads

    monkeypatch.setattr(uploads.urllib.request, "urlopen", lambda request, timeout, context: io.BytesIO(ROSTER.read_bytes()))
    name, data, count = uploads.fetch_jail_roster()
    assert name.startswith("jail_roster_") and name.endswith(".html") and count == 3


def test_jail_log_fetch_failure_gives_a_plain_message(monkeypatch):
    import pytest
    from leads import uploads

    def offline(request, timeout, context):
        raise uploads.urllib.error.URLError("no network")
    monkeypatch.setattr(uploads.urllib.request, "urlopen", offline)
    with pytest.raises(uploads.FetchFailed, match="Could not reach the county jail roster"):
        uploads.fetch_jail_roster()


def test_optional_sets_join_the_collection_and_keep_their_pdfs(tmp_path):
    text_dir, _ = build_collection([], uploads_root=tmp_path, sample_sets=["hilton_head", "school_board"])
    store = DocumentStore(text_dir)
    hhi = [d for d in store.docs.values() if d.doc_type == "Hilton Head Island Town Council minutes"]
    board = [d for d in store.docs.values() if d.doc_type == "Beaufort County School District board agenda"]
    assert len(hhi) == 21 and len(board) == 19
    assert all(d.source_file.endswith(".pdf") for d in hhi + board)
    assert "Hilton Head Island Town Council minutes" in store.notes


def test_quotes_from_an_optional_set_can_be_verified(tmp_path):
    text_dir, _ = build_collection([], uploads_root=tmp_path, sample_sets=["school_board"])
    store = DocumentStore(text_dir)
    hits = tools.search_documents(store, "8% CIP funds")
    assert hits["total_matches"] > 0
    first = hits["results"][0]["doc_id"]
    quote = "8% CIP funds"
    page_text = " ".join(store.get(first).pages)
    assert quote in page_text


def test_added_documents_are_marked_and_searched_newest_first(tmp_path):
    text_dir, _ = build_collection([], uploads_root=tmp_path, sample_sets=["hilton_head"])
    store = DocumentStore(text_dir)
    listing = {d["doc_id"]: d["added_by_journalist"] for d in tools.list_documents(store)["documents"]}
    assert listing["2026-01-12_council_minutes_1544"] is False  # built-in county minutes
    assert listing["2026-01-13_hhi-town-council_regular_minutes_1072"] is True
    dates = [r["date"] for r in tools.search_documents(store, "Council")["results"]]
    assert dates == sorted(dates, reverse=True) and dates[0].startswith("2026")


def test_the_2020_2022_archive_joins_with_its_project_lists_and_pdfs(tmp_path):
    text_dir, _ = build_collection([], uploads_root=tmp_path, sample_sets=["county_archive"])
    store = DocumentStore(text_dir)
    trackers = [d for d in store.docs.values() if d.doc_type.startswith("Capital project tracker")]
    assert len(trackers) == 7 and all(d.source_file.endswith(".pdf") for d in trackers)
    assert store.get("2026-01-12_council_minutes_1544").source_file.endswith(".pdf")
    assert "December 2020 to April 2022" in store.notes  # the archive's own notes come along
