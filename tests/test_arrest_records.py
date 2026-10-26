"""Arrest-record leads: only from an uploaded jail log, charges quoted exactly, never a presumption of guilt."""

from leads import config
from leads.pipeline import run_investigation
from leads.uploads import build_collection
from tests.test_pipeline import ScriptedClient, keep, tool_call_response

LOG = config.PROJECT_DIR / "test_fixtures" / "uploads" / "sample_jail_log_2023-06-02.txt"
ENTRY = ("Name: Darnell Hughes | Age: 37 | Booked: 06/02/2023 09:05 | Arresting agency: Port Harlow County "
         "Sheriff's Office | Charges: Breach of trust with fraudulent intent")


def arrest(lead_id, title, doc_id, quote=ENTRY, summary="Booked on breach of trust charges; employer listed as "
                                                          "the county's paving contractor."):
    return {"lead_id": lead_id, "title": title, "lead_type": "arrest_record", "project": "", "summary": summary,
            "amount_before": "", "amount_after": "", "searched_for": "Darnell Hughes; Coastal Asphalt",
            "news_values": ["Prominence"], "why_it_surfaced": "Employer is a county contractor.",
            "evidence": [{"doc_id": doc_id, "quote": quote, "what_it_shows": "booking entry"}]}


def run(tmp_path, leads):
    text_dir, report = build_collection([(LOG.name, LOG.read_bytes())], base_dir=config.FIXTURE_DATA_DIR,
                                        uploads_root=tmp_path / "uploads")
    script = [tool_call_response("submit_candidates", {"candidates": [], "notes": ""}),
              tool_call_response("submit_leads", {"leads": leads, "dropped": []}),
              tool_call_response("submit_verdicts", {"verdicts": [keep(lead["lead_id"]) for lead in leads]})]
    result = run_investigation("Public safety", data_dir=text_dir, client=ScriptedClient(script),
                               runs_dir=tmp_path / "runs")
    return result, report[0]["doc_id"]


def test_arrest_from_uploaded_log_is_shown_with_the_notice(tmp_path):
    doc_id = build_collection([(LOG.name, LOG.read_bytes())], base_dir=config.FIXTURE_DATA_DIR,
                              uploads_root=tmp_path / "probe")[1][0]["doc_id"]
    result, _ = run(tmp_path, [arrest("A1", "Paving contractor employee booked on breach of trust charges", doc_id)])
    card = result.leads[0]
    assert card["lead_type"] == "Arrest record"
    assert card["notice"] == config.ARREST_NOTICE  # set by code on every arrest card
    assert "fraudulent intent" in card["evidence"][0]["quote"]  # the charge is kept, quoted exactly


def test_arrest_lead_not_from_an_upload_is_killed(tmp_path):
    quote = "Committee Chair Calloway asked why the committee was not informed of the Harbor Park Pavilion overrun"
    result, _ = run(tmp_path, [arrest("A2", "Made-up arrest", "2023-06-19_finance_minutes", quote=quote)])
    assert result.leads == []
    assert "jail log or booking report" in result.killed[0]["reason"]


def test_card_that_presumes_guilt_is_killed(tmp_path):
    doc_id = build_collection([(LOG.name, LOG.read_bytes())], base_dir=config.FIXTURE_DATA_DIR,
                              uploads_root=tmp_path / "probe")[1][0]["doc_id"]
    result, _ = run(tmp_path, [arrest("A3", "Contractor employee guilty of fraud", doc_id)])
    assert result.leads == [] and "guilty" in result.killed[0]["reason"]


def test_invented_charge_is_dropped(tmp_path):
    doc_id = build_collection([(LOG.name, LOG.read_bytes())], base_dir=config.FIXTURE_DATA_DIR,
                              uploads_root=tmp_path / "probe")[1][0]["doc_id"]
    invented = "Name: Darnell Hughes | Charges: Bribery of a public official (3 counts)"
    result, _ = run(tmp_path, [arrest("A4", "Contractor employee booked", doc_id, quote=invented)])
    assert result.leads == [] and "word for word" in result.killed[0]["reason"]
