"""The full Scout -> Connector -> Skeptic -> code-check pipeline, driven by a scripted fake model.

No API calls: the fake model replays fixed tool calls, so we can test exactly what the
plain-code checks do with good, invented, small, and accusatory leads.
"""

import json

from openai.types.chat import ChatCompletion

from leads import config
from leads.pipeline import run_investigation

GOOD_QUOTE_A = ("EMS Station 31 | Description: Construction of joint EMS and Fire Station located on Riverside, "
                "Bluffton | Project Cost: $1,650,547")
GOOD_QUOTE_B = ("EMS Station 31 | Description: Construction of joint EMS and Fire Station located on Riverside, "
                "Bluffton | Project Cost: $3,585,813")


def lead(lead_id, title, before="$1,650,547", after="$3,585,813", quote_b=GOOD_QUOTE_B, summary="Cost doubled."):
    return {"lead_id": lead_id, "title": title, "lead_type": "change", "project": "EMS Station 31",
            "summary": summary, "amount_before": before, "amount_after": after,
            "evidence": [{"doc_id": "tracker_2020-12-04", "quote": GOOD_QUOTE_A, "what_it_shows": "before"},
                         {"doc_id": "tracker_2021-01-08", "quote": quote_b, "what_it_shows": "after"}],
            "searched_for": "Station 31", "news_values": ["Impact"], "why_it_surfaced": "Large jump."}


def keep(lead_id, **extra):
    return {"lead_id": lead_id, "verdict": "keep", "reason": "Survives.", "alternative_explanation": "Fire district share.",
            "next_steps": ["Request the contract."], "exception_news_value": "", "exception_doc_id": "",
            "exception_quote": "", **extra}


ADA = ("ADA Ramp Improvements | Description: Ramp installation for sidewalk at the intersections of Ninth Avenue "
       "at Red Cedar. Installation of pedestrian crosswalk signals. | Project Cost: ")
SMALL = {**lead("L3", "Small change", before="$27,451", after="$47,981"),
         "evidence": [{"doc_id": "tracker_2021-03-05", "quote": ADA + "$27,451", "what_it_shows": "before"},
                      {"doc_id": "tracker_2021-05-10", "quote": ADA + "$47,981", "what_it_shows": "after"}]}

LEADS = [
    lead("L1", "EMS Station 31 cost doubled"),
    lead("L2", "Invented quote", quote_b="EMS Station 31 cost was secretly raised to $3,585,813 by staff"),
    SMALL,
    lead("L4", "Accusatory wording", summary="This looks like fraud."),
    lead("L5", "Skeptic kills this one"),
]
VERDICTS = [keep("L1"), keep("L2"), keep("L3"), keep("L4"),
            {**keep("L5"), "verdict": "kill", "reason": "Explained by contingency."}]


def tool_call_response(name, args, call_id="c1", tokens=500):
    return ChatCompletion.model_validate({
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-6-luna",
        "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
            "role": "assistant", "content": None,
            "tool_calls": [{"id": call_id, "type": "function",
                            "function": {"name": name, "arguments": json.dumps(args)}}]}}],
        "usage": {"prompt_tokens": tokens, "completion_tokens": 50, "total_tokens": tokens + 50},
    })


class ScriptedClient:
    """Plays back one response per model call, in order."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.chat = self
        self.completions = self

    def create(self, **request):
        return self.responses.pop(0)


SCRIPT = [
    tool_call_response("search_documents", {"keyword": "EMS Station 31"}),  # Scout uses a tool
    tool_call_response("submit_candidates", {"candidates": [], "notes": ""}),  # Scout hands off
    tool_call_response("submit_leads", {"leads": LEADS, "dropped": [{"title": "Weak one", "reason": "No support"}]}),
    tool_call_response("submit_verdicts", {"verdicts": VERDICTS}),
]


def run(tmp_path, script=SCRIPT, **kwargs):
    return run_investigation("Public spending", client=ScriptedClient(script), runs_dir=tmp_path, **kwargs)


def test_only_the_solid_lead_reaches_the_journalist(tmp_path):
    result = run(tmp_path)
    assert result.status == "complete"
    assert [card["title"] for card in result.leads] == ["EMS Station 31 cost doubled"]


def test_every_kill_is_logged_with_a_reason(tmp_path):
    reasons = {k["title"]: (k["killed_by"], k["reason"]) for k in run(tmp_path).killed}
    # Its real "before" quote passes, but the invented "after" quote is dropped, leaving $3,585,813 unsupported.
    assert reasons["Invented quote"][0] == "App" and "$3,585,813" in reasons["Invented quote"][1]
    assert reasons["Small change"][0] == "App" and "below the $30,000" in reasons["Small change"][1]
    assert reasons["Accusatory wording"][0] == "App" and "fraud" in reasons["Accusatory wording"][1]
    assert reasons["Skeptic kills this one"] == ("Skeptic", "Explained by contingency.")
    assert reasons["Weak one"] == ("Connector", "No support")
    assert json.loads((tmp_path / run(tmp_path).run_id / "killed_leads.json").read_text())


def test_card_has_every_field_and_fixed_confidence(tmp_path):
    card = run(tmp_path).leads[0]
    for name in ["lead", "why_it_surfaced", "evidence", "alternative_explanation", "next_steps", "confidence"]:
        assert card[name]
    assert card["confidence"] == config.CONFIDENCE_LABEL
    assert card["evidence"][0]["file"] == "tracker_2020-12-04.pdf"
    assert card["dollar_change"] == 1_935_266


def test_small_change_survives_with_a_verified_news_value(tmp_path):
    verdicts = [*VERDICTS[:2], keep("L3", exception_news_value="Human interest",
                                    exception_doc_id="tracker_2021-05-10",
                                    exception_quote="Installation of pedestrian crosswalk signals."), *VERDICTS[3:]]
    script = [*SCRIPT[:3], tool_call_response("submit_verdicts", {"verdicts": verdicts})]
    titles = [card["title"] for card in run(tmp_path, script=script).leads]
    assert "Small change" in titles


def test_trace_records_each_handoff(tmp_path):
    result = run(tmp_path)
    trace = json.loads((result.run_dir / "trace.json").read_text())
    handoffs = [e["actor"] for e in trace if e["kind"] == "handoff"]
    assert handoffs == ["Scout", "Connector", "Skeptic"]
    assert (result.run_dir / "trace.md").exists()


def test_token_budget_stops_the_run_cleanly(tmp_path):
    # Each fake call reports 5,550 tokens; a 6,000-token budget allows two calls, then stops.
    script = [tool_call_response("search_documents", {"keyword": "pool"}, tokens=5_500)] * 2 + SCRIPT[1:]
    result = run(tmp_path, script=script, token_budget=6_000, fresh=True)
    assert result.status == "stopped"
    assert "budget" in result.message and result.leads == []


def test_missing_key_gives_a_plain_message(tmp_path, monkeypatch):
    monkeypatch.setattr("leads.pipeline.load_api_key",
                        lambda: (_ for _ in ()).throw(__import__("leads.llm", fromlist=["MissingKey"]).MissingKey("No key")))
    result = run_investigation("Development", runs_dir=tmp_path)
    assert result.status == "error" and result.message == "No key"


def scout_says(tmp_path, notes, suspicious):
    script = [tool_call_response("submit_candidates", {"candidates": [], "notes": notes,
                                                       "suspicious_documents": suspicious}), *SCRIPT[2:]]
    return run_investigation("Public spending", data_dir=config.FIXTURE_DATA_DIR,
                             client=ScriptedClient(script), runs_dir=tmp_path)


def test_no_false_alarm_when_scout_says_nothing_suspicious(tmp_path):
    assert scout_says(tmp_path, "No suspicious instructions found.", []).warnings == []


def test_real_injection_document_is_named_in_the_warning(tmp_path):
    warnings = scout_says(tmp_path, "", ["2023-05-15_pubfac_minutes"]).warnings
    assert warnings == ["Suspicious instructions found in 2023-05-15_pubfac_minutes.txt; they were ignored."]


def test_made_up_document_name_cannot_raise_an_alarm(tmp_path):
    assert scout_says(tmp_path, "", ["not_a_real_file"]).warnings == []


def test_worth_a_closer_look_lead_passes_checks_without_dollar_figures(tmp_path):
    quote = "Committee Chair Calloway asked why the committee was not informed of the Harbor Park Pavilion overrun"
    notable = {"lead_id": "N1", "title": "Finance chair says committee was kept in the dark on overrun",
               "lead_type": "notable", "project": "Harbor Park Pavilion", "summary": "The chair objected.",
               "amount_before": "", "amount_after": "", "searched_for": "", "news_values": ["Conflict"],
               "why_it_surfaced": "Officials disagree.",
               "evidence": [{"doc_id": "2023-06-19_finance_minutes", "quote": quote, "what_it_shows": "objection"}]}
    script = [tool_call_response("submit_candidates", {"candidates": [], "notes": ""}),
              tool_call_response("submit_leads", {"leads": [notable], "dropped": []}),
              tool_call_response("submit_verdicts", {"verdicts": [keep("N1")]})]
    result = run_investigation("Local government", data_dir=config.FIXTURE_DATA_DIR,
                               client=ScriptedClient(script), runs_dir=tmp_path)
    assert [c["lead_type"] for c in result.leads] == ["Worth a closer look"]
