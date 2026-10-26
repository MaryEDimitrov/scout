"""The agents' tools, run on the real Beaufort County documents (no model calls)."""

from leads import config, tools
from leads.documents import DocumentStore

STORE = DocumentStore(config.ARCHIVE_DATA_DIR)


def test_collection_loads():
    listing = tools.list_documents(STORE)["documents"]
    types = [d["type"] for d in listing]
    assert len(listing) >= 27
    assert types.count("Capital project tracker (dated snapshot)") >= 7


def test_search_finds_the_arthur_horne_overage():
    result = tools.search_documents(STORE, "Arthur Horne Building overage")
    assert any(r["doc_id"] == "2022-03-21_finance_packet_360_p22-25" for r in result["results"])


def test_fort_and_ft_are_the_same_word():
    result = tools.lookup_project(STORE, "Fort Fremont Interpretive Center")
    assert "tracker_2020-12-04" in result["documents_mentioning"]


def test_compare_does_the_arithmetic():
    result = tools.compare_passages(
        STORE,
        "tracker_2020-12-04", "EMS Station 31 | Description: Construction of joint EMS and Fire Station "
                              "located on Riverside, Bluffton | Project Cost: $1,650,547",
        "tracker_2021-01-08", "EMS Station 31 | Description: Construction of joint EMS and Fire Station "
                              "located on Riverside, Bluffton | Project Cost: $3,585,813",
    )
    assert result["a"]["quote_found_in_source"] and result["b"]["quote_found_in_source"]
    assert result["change"]["difference"] == 1_935_266
    assert result["change"]["below_threshold"] is False


def test_small_change_is_marked_below_threshold():
    result = tools.compare_passages(
        STORE,
        "tracker_2021-03-05", "ADA Ramp Improvements | Description",  # quote without a figure
        "tracker_2021-05-10", "Project Cost: $47,981",
    )
    assert isinstance(result["change"], str)  # no figure on one side: no arithmetic
    result = tools.compare_passages(STORE, "tracker_2021-03-05", "Project Cost: $27,451",
                                    "tracker_2021-05-10", "Project Cost: $47,981")
    assert result["change"]["below_threshold"] is True


def test_fetch_passage_returns_context_and_page():
    result = tools.fetch_passage(STORE, "2022-03-21_finance_packet_360_p22-25", "Arthur Horne Building overage 900,000")
    assert result["found"] and result["page"] == 2
    assert "M.C. Riley Pool" in result["passage_with_context"]


def test_fetch_passage_reports_missing_quote():
    result = tools.fetch_passage(STORE, "tracker_2022-04-01", "Arthur Horne overage $900,000")
    assert result["found"] is False


def test_bad_document_name_gives_a_helpful_error():
    result = tools.read_section(STORE, "not_a_file", 1)
    assert "list_documents" in result["error"]


def test_lookup_falls_back_to_key_words_in_any_order():
    result = tools.lookup_project(STORE, "Change Order 2 Myrtle Park paving")  # not written this way anywhere
    assert result["matched_by"].startswith("all key words")
    assert "2022-02-07_exec_minutes_293" in result["documents_mentioning"]


def test_current_project_lists_are_in_the_built_in_collection():
    store = DocumentStore(config.CURRENT_DATA_DIR)
    types = {d.doc_type for d in store.docs.values()}
    assert any(t.startswith("Capital projects dashboard") for t in types)
    assert any(t.startswith("Capital Improvement Plan") for t in types)
    hits = tools.search_documents(store, "Buckwalter Recreation Athletic Complex")
    assert any(r["doc_id"].startswith("project_list_") for r in hits["results"])
