"""One investigation run: Scout -> Connector -> Skeptic -> plain-code checks -> lead cards.

    Journalist picks an area
        -> Scout      (list_documents, search_documents, read_section)   hands off: candidates
        -> Connector  (lookup_project, compare_passages)                  hands off: leads with evidence
        -> Skeptic    (fetch_passage)                                     hands off: keep/kill verdicts
        -> Code checks (verbatim quotes, $30K rule, no accusations, fixed confidence)
        -> Lead cards shown to the journalist; killed leads logged with the reason
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import openai

from . import config
from .agents import AgentError, RunContext, run_agent
from .documents import DocumentStore, dollars_to_number
from .jail import flag_bookings
from .guards import BudgetExceeded, TokenBudget, ToolCallCounter
from .llm import LLM, MissingKey, UsageLog, load_api_key, make_client
from .trace import Trace
from .verify import check_quote, normalize, verify_lead

AREAS = {  # beats modeled on what the Island Packet, Beaufort Gazette, and The State cover
    "Public spending": "project costs, contracts, change orders, budget amendments, and funding sources",
    "Events, openings & closings": "fun and newsworthy upcoming events, grand openings, and closings or cancellations "
                                   "from the Beaufort County, Hilton Head Island, and Port Royal calendars",
    "Growth & development": "construction projects, site development, land, public buildings, and growth pressures",
    "Local government": "what Council and its committees approved, awarded, questioned, or were told",
    "Education": "school buildings and renovations, school board decisions, libraries, and education spending",
    "Environment & climate": "flooding, drainage and stormwater, preserves, parks and conservation land, and resilience",
    "Transportation": "roads, paving, sales-tax road projects, pathways, sidewalks, bridges, and airports",
    "Housing": "affordable and workforce housing, property purchases for housing, and housing-related spending",
    "Public safety": "spending on EMS and fire stations, the sheriff's office, and detention facilities; "
                     "newsworthy arrests if the journalist uploaded a jail log or booking report",
}
ACCUSATORY = re.compile(r"\b(fraud\w*|corrupt\w*|illegal\w*|embezzl\w*|cover[- ]?up|kickback\w*|"
                        r"lied|lying|stole|theft|crimin\w*|misconduct)\b", re.IGNORECASE)
# Arrest-record cards may name charges, but must never presume guilt.
PRESUMES_GUILT = re.compile(r"\b(guilty|convicted|perpetrator|culprit|committed (?:the|a|an)\b|"
                            r"is a criminal|broke the law)", re.IGNORECASE)
LEAD_TYPE_LABELS = {"change": "Change", "missing_link": "Missing link", "notable": "Worth a closer look",
                    "event": "Event", "opening_closing": "Opening or closing", "arrest_record": "Arrest record"}
UPLOADED = "Uploaded by the journalist"


@dataclass
class RunResult:
    run_id: str
    status: str  # "complete", "stopped", or "error"
    message: str  # plain-language message for the journalist
    leads: list[dict] = field(default_factory=list)
    killed: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    usage_summary: list[dict] = field(default_factory=list)
    run_dir: Path | None = None
    area: str = ""
    data: str = "real"  # "real" Beaufort County records or "fixtures" (synthetic test documents)
    fresh: bool = False
    jail: dict = field(default_factory=dict)  # jail-log summary: bookings checked, flagged, ICE holds


def run_investigation(area: str, data_dir: Path = config.CURRENT_DATA_DIR, fresh: bool = False,
                      client=None, token_budget: int = config.TOKEN_BUDGET_PER_RUN,
                      on_progress=lambda stage, fraction: None, runs_dir: Path = config.RUNS_DIR) -> RunResult:
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + re.sub(r"\W+", "-", area.lower())
    run_dir = runs_dir / run_id
    trace = Trace(run_id, run_dir)
    usage = UsageLog(run_id, log_file=runs_dir / "token_log.csv")
    result = RunResult(run_id, "error", "", run_dir=run_dir, area=area, fresh=fresh,
                       data=data_source(Path(data_dir)))
    # A fresh run adds its run id at the END of each task, so nothing is replayed from a cache
    # while the long stable instructions at the start can still be cached by the provider.
    tag = f"\n\n(Run id: {run_id})" if fresh else ""

    try:
        store = DocumentStore(data_dir)
        if not store.docs:
            result.message = f"No documents found in {data_dir}. Check that the data folder is in place."
            return result
        client = client or make_client(load_api_key())
        ctx = RunContext(LLM(client, usage, TokenBudget(token_budget), use_cache=not fresh,
                             cache_dir=runs_dir / "cache"),
                         store, ToolCallCounter(), trace,
                         on_progress=lambda msg: on_progress(msg, None))
        trace.add("Journalist", "start", f"Area of interest: {area}. {len(store.docs)} documents. Fresh run: {fresh}.")

        on_progress("Scout is scanning the records…", 0.1)
        scout = run_agent(ctx, "Scout", f"Area of interest chosen by the journalist: {area} "
                          f"({AREAS.get(area, area)}).\nFind candidate leads.{tag}",
                          ["list_documents", "search_documents", "read_section"])
        candidates = scout.get("candidates", [])
        # The newsroom's arrest list is applied to any jail log in plain code, not left to the AI.
        jail_candidates, jail_summary = flag_bookings(store)
        if jail_summary["bookings_checked"]:
            candidates = [c for c in candidates if c.get("lead_type") != "arrest_record"] + jail_candidates
            result.jail = jail_summary
            trace.add("App", "code_check", f"Jail log: checked {jail_summary['bookings_checked']} bookings against the "
                      f"newsroom's list; {jail_summary['flagged']} flagged for the Connector", jail_summary)
        trace.add("Scout", "handoff", f"{len(candidates)} candidates → Connector: "
                  + "; ".join(c["title"] for c in candidates), scout)
        for doc_id in scout.get("suspicious_documents", []):
            if doc := store.get(doc_id):  # only real documents, so a made-up name can't raise a false alarm
                result.warnings.append(f"Suspicious instructions found in {doc.source_file}; they were ignored.")
                trace.add("Scout", "code_check", f"Flagged suspicious instructions in {doc.source_file}")

        on_progress("Connector is linking evidence across documents…", 0.4)
        connector = run_agent(ctx, "Connector", "Candidates from the Scout:\n"
                              + json.dumps(candidates, indent=1) + tag, ["lookup_project", "compare_passages"])
        leads = connector.get("leads", [])
        trace.add("Connector", "handoff", f"{len(leads)} leads → Skeptic; {len(connector.get('dropped', []))} dropped",
                  connector)

        on_progress("Skeptic is trying to disprove each lead…", 0.7)
        skeptic = run_agent(ctx, "Skeptic", "Leads from the Connector:\n" + json.dumps(leads, indent=1) + tag,
                            ["fetch_passage"])
        verdicts = {v["lead_id"]: v for v in skeptic.get("verdicts", [])}
        trace.add("Skeptic", "handoff",
                  f"{sum(v['verdict'] == 'keep' for v in verdicts.values())} kept, "
                  f"{sum(v['verdict'] == 'kill' for v in verdicts.values())} killed → code checks", skeptic)

        on_progress("Checking every quote against the source files…", 0.9)
        result.leads, result.killed = apply_code_checks(store, leads, verdicts, trace)
        result.killed += [{"title": d["title"], "killed_by": "Connector", "reason": d["reason"]}
                          for d in connector.get("dropped", [])]
        result.status = "complete"
        result.message = (f"{len(result.leads)} lead(s) surfaced. {len(result.killed)} possible lead(s) were "
                          "dismissed; see the log of dismissed leads for the reasons.")
    except BudgetExceeded as stop:
        result.status, result.message = "stopped", f"{stop} No unchecked leads are shown."
    except MissingKey as problem:
        result.message = str(problem)
    except openai.AuthenticationError:
        result.message = "The API key was rejected. Check PORTKEY_API_KEY in your .env file."
    except openai.RateLimitError:
        result.message = "The AI service is busy or the account is over its limit. Wait a minute and try again."
    except openai.APITimeoutError:
        result.message = "The AI service took too long to answer. Try again in a minute."
    except openai.APIConnectionError:
        result.message = "Could not reach the AI service. Check your internet connection and try again."
    except openai.APIError as problem:
        result.message = f"The AI service returned an error ({type(problem).__name__}). Try again in a minute."
    except AgentError as problem:
        result.message = f"{problem} Try running again."
    except Exception as problem:  # never show the journalist a crash screen
        result.message = "Something went wrong during the run. Try again; if it keeps happening, check the run trace."
        trace.add("App", "stop", f"Unexpected error: {type(problem).__name__}: {problem}")
    finally:
        trace.add("App", "finish", result.message)
        result.usage_summary = usage.summary()
        save_run(result, trace)
        on_progress("Done", 1.0)
    return result


def data_source(data_dir: Path) -> str:
    """Label runs so measured costs only count the plain real collection."""
    if data_dir == config.FIXTURE_DATA_DIR:
        return "fixtures"
    return "real" if data_dir == config.CURRENT_DATA_DIR else "real+uploads"


def apply_code_checks(store: DocumentStore, leads: list[dict], verdicts: dict, trace: Trace):
    """The last word belongs to plain code, not the model."""
    kept, killed = [], []

    def kill(lead, by, reason):
        killed.append({"title": lead.get("title", ""), "lead_id": lead.get("lead_id", ""),
                       "killed_by": by, "reason": reason})
        trace.add(by, "verdict", f"KILLED '{lead.get('title', '')}': {reason}")

    for lead in leads:
        verdict = verdicts.get(lead["lead_id"])
        if verdict is None:
            kill(lead, "App", "The Skeptic did not review this lead, so it is not shown.")
            continue
        if verdict["verdict"] == "kill":
            kill(lead, "Skeptic", verdict["reason"])
            continue

        # 1. Every quote must appear word for word in its source file; drop any that do not.
        verify_lead(store, lead)
        bad = [e for e in lead["evidence"] if not e["verified"]]
        lead["evidence"] = [e for e in lead["evidence"] if e["verified"]]
        for e in bad:
            trace.add("App", "code_check", f"Dropped an unverifiable quote from '{lead['title']}' ({e['doc_id']})", e)
        if not lead["evidence"]:
            kill(lead, "App", "None of its evidence quotes could be found word for word in the source files.")
            continue
        lead["quotes_removed"] = len(bad)
        verified_text = " ".join(normalize(e["quote"]) for e in lead["evidence"])
        unsupported = [a for a in (lead["amount_before"], lead["amount_after"]) if a and a not in verified_text]
        if unsupported:
            kill(lead, "App", f"Its dollar figure(s) {', '.join(unsupported)} do not appear in any quote that "
                              "could be found word for word in the source files.")
            continue

        # 2. Arrest records may only come from a jail log or booking report the journalist uploaded.
        is_arrest = lead["lead_type"] == "arrest_record"
        if is_arrest and not any(store.get(e["doc_id"]).doc_type == UPLOADED for e in lead["evidence"]):
            kill(lead, "App", "Arrest records may only come from a jail log or booking report the journalist "
                              "uploaded; this lead had no verified quote from one.")
            continue

        # 3. The $30K rule, enforced in code.
        change = dollar_change(lead)
        if change is not None and abs(change) < config.MIN_DOLLAR_CHANGE:
            ok = bool(verdict["exception_news_value"]) and check_quote(
                store, verdict["exception_doc_id"], verdict["exception_quote"])[0]
            if not ok:
                kill(lead, "App", f"Change of ${abs(change):,.0f} is below the ${config.MIN_DOLLAR_CHANGE:,} "
                                  "threshold, with no verified news value to justify it.")
                continue
            trace.add("App", "code_check", f"Kept small change in '{lead['title']}' for news value: "
                      f"{verdict['exception_news_value']}")

        # 4. No accusations anywhere on the card. Arrest cards may state recorded charges, never guilt.
        card_text = " ".join([lead["title"], lead["summary"], lead["why_it_surfaced"],
                              verdict["alternative_explanation"], *verdict["next_steps"]])
        banned = (PRESUMES_GUILT if is_arrest else ACCUSATORY).search(card_text)
        if banned:
            kill(lead, "App", f"Wording on the card was accusatory ('{banned.group(0)}').")
            continue

        kept.append(make_card(store, lead, verdict, change))
        trace.add("App", "code_check", f"Passed all checks: '{lead['title']}'")

    kept.sort(key=lambda c: (len(c["news_values"]), abs(c["dollar_change"] or 0)), reverse=True)
    return kept, killed


def dollar_change(lead: dict) -> float | None:
    try:
        return dollars_to_number(lead["amount_after"]) - dollars_to_number(lead["amount_before"])
    except (ValueError, KeyError):
        return None


def make_card(store: DocumentStore, lead: dict, verdict: dict, change: float | None) -> dict:
    return {
        "lead_id": lead["lead_id"],
        "lead_type": LEAD_TYPE_LABELS[lead["lead_type"]],
        "title": lead["title"],
        "project": lead.get("project", ""),
        "lead": lead["summary"],
        "why_it_surfaced": lead["why_it_surfaced"],
        "news_values": lead["news_values"],
        "evidence": [{"file": store.get(e["doc_id"]).source_file, "doc_id": e["doc_id"],
                      "quote": normalize(e["quote"]), "what_it_shows": e["what_it_shows"]} for e in lead["evidence"]],
        "searched_for": lead["searched_for"],
        "alternative_explanation": verdict["alternative_explanation"],
        "next_steps": verdict["next_steps"],
        "skeptic_note": verdict["reason"],
        "amount_before": lead["amount_before"],
        "amount_after": lead["amount_after"],
        "dollar_change": change,
        "quotes_removed": lead["quotes_removed"],  # quotes dropped because they were not found verbatim
        "confidence": config.CONFIDENCE_LABEL,  # set here, never by the model
        "notice": config.ARREST_NOTICE if lead["lead_type"] == "arrest_record" else "",  # set here too
    }


def save_run(result: RunResult, trace: Trace) -> None:
    run_dir = result.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "leads.json").write_text(json.dumps(result.leads, indent=2))
    (run_dir / "killed_leads.json").write_text(json.dumps(result.killed, indent=2))
    (run_dir / "usage.json").write_text(json.dumps(result.usage_summary, indent=2))
    (run_dir / "result.json").write_text(json.dumps(
        {"run_id": result.run_id, "area": result.area, "data": result.data, "fresh": result.fresh,
         "status": result.status, "message": result.message, "warnings": result.warnings}, indent=2))
    trace.save()
