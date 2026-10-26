"""Safety feature 2 (invented facts): evidence quotes must appear verbatim in the source."""

from leads import config
from leads.documents import DocumentStore
from leads.verify import check_quote, verify_lead

STORE = DocumentStore(config.REAL_DATA_DIR)
FINANCE = "2022-03-21_finance_minutes_360"
REAL_QUOTE = "Committee Chairman Lawson asked about the overage on the Arthur Horne Building"


def test_real_quote_passes():
    ok, _ = check_quote(STORE, FINANCE, REAL_QUOTE)
    assert ok


def test_line_breaks_and_extra_spaces_do_not_matter():
    reflowed = REAL_QUOTE.replace(" about the ", "\n  about\tthe ")
    ok, _ = check_quote(STORE, FINANCE, reflowed)
    assert ok


def test_straight_apostrophe_matches_curly_one_in_source():
    # The tracker PDF prints "Lady’s" with a curly apostrophe; the model often types a straight one.
    ok, _ = check_quote(STORE, "tracker_2021-11-05", "Project Name: Lady's Island Access Roads")
    assert ok


def test_apostrophe_exception_does_not_hide_a_changed_word():
    ok, _ = check_quote(STORE, "tracker_2021-11-05", "Project Name: Lady's Island Access Road |")  # "Roads" in source
    assert not ok


def test_changed_number_fails():
    ok, reason = check_quote(STORE, "tracker_2022-04-01", "Arthur Horne Office Building | Description")
    assert ok  # sanity check: the real text is there
    ok, reason = check_quote(STORE, "tracker_2022-04-01", "Project Cost: $6,775,813")  # real figure is $6,775,812
    assert not ok and "word-for-word" in reason


def test_invented_quote_fails():
    ok, _ = check_quote(STORE, FINANCE, "Council voted to hide the Arthur Horne overage from the public")
    assert not ok


def test_quote_from_the_wrong_document_fails():
    ok, _ = check_quote(STORE, "tracker_2020-12-04", REAL_QUOTE)
    assert not ok


def test_unknown_document_fails():
    ok, reason = check_quote(STORE, "made_up_file", REAL_QUOTE)
    assert not ok and "No document" in reason


def test_too_short_quote_fails():
    ok, reason = check_quote(STORE, FINANCE, "$900")
    assert not ok and "too short" in reason


def test_lead_with_one_bad_quote_is_flagged():
    lead = {"evidence": [
        {"doc_id": FINANCE, "quote": REAL_QUOTE},
        {"doc_id": FINANCE, "quote": "The overage was $5 million and nobody was told"},
    ]}
    verify_lead(STORE, lead)
    assert lead["evidence"][0]["verified"] is True
    assert lead["evidence"][1]["verified"] is False
    assert lead["all_evidence_verified"] is False
