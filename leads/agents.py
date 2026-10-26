"""The three agents. Each one is the same simple loop with different instructions and tools.

Loop: send instructions + task to the model -> the model calls tools -> we run them and send back
the results -> repeat until the model calls its "submit" tool with its handoff for the next agent.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import tools
from .documents import DocumentStore
from .guards import ToolCallCounter, ToolLimitReached
from .llm import LLM
from .trace import Trace

PROMPTS = Path(__file__).parent / "prompts"
NEWS_VALUES = ["Impact", "Conflict", "Timeliness", "Proximity", "Prominence", "Unusual",
               "Currency", "Human interest", "Verified evidence"]  # "So what" is a test, not a tag


class AgentError(Exception):
    """An agent finished without handing anything off."""


# ---------------------------------------------------------------- tool descriptions for the model

def _tool(name: str, description: str, properties: dict) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description, "strict": True,
        "parameters": {"type": "object", "properties": properties,
                       "required": list(properties), "additionalProperties": False},
    }}


STR = {"type": "string"}
QUOTE = {"type": "object", "properties": {"doc_id": STR, "quote": STR},
         "required": ["doc_id", "quote"], "additionalProperties": False}
LEAD_TYPE = {"type": "string", "enum": ["change", "missing_link", "notable", "event", "opening_closing",
                                       "arrest_record"]}
NEWS = {"type": "array", "items": {"type": "string", "enum": NEWS_VALUES}}

TOOL_SCHEMAS = {
    "list_documents": _tool("list_documents", "List every document with its type, date, and page count.", {}),
    "search_documents": _tool(
        "search_documents", "Find a keyword or phrase across all documents. Returns short snippets.",
        {"keyword": STR}),
    "read_section": _tool(
        "read_section", "Read one page of a document.",
        {"doc_id": STR, "page": {"type": "integer"}}),
    "compare_passages": _tool(
        "compare_passages",
        "Compare two exact quotes from two documents. Checks both quotes exist and computes the "
        "dollar difference, percent change, and whether it is below the $30,000 threshold.",
        {"doc_a": STR, "quote_a": STR, "doc_b": STR, "quote_b": STR}),
    "lookup_project": _tool(
        "lookup_project",
        "Find every mention of a project name across the collection, with dollar figures and approval "
        "words (approve, award, change order, ordinance...) near each mention.",
        {"name": STR}),
    "fetch_passage": _tool(
        "fetch_passage", "Fetch the exact source passage for a quote, with the text around it.",
        {"doc_id": STR, "quote": STR}),
}

SUBMIT = {
    "Scout": _tool("submit_candidates", "Hand your candidate leads to the Connector.", {
        "candidates": {"type": "array", "items": {"type": "object", "properties": {
            "title": STR, "lead_type": LEAD_TYPE, "project": STR, "what_caught_my_eye": STR,
            "news_values": NEWS, "pointers": {"type": "array", "items": QUOTE},
        }, "required": ["title", "lead_type", "project", "what_caught_my_eye", "news_values", "pointers"],
            "additionalProperties": False}},
        "notes": STR,
        "suspicious_documents": {"type": "array", "items": STR},  # doc_ids containing instructions aimed at the AI
    }),
    "Connector": _tool("submit_leads", "Hand your evidence-backed leads to the Skeptic.", {
        "leads": {"type": "array", "items": {"type": "object", "properties": {
            "lead_id": STR, "title": STR, "lead_type": LEAD_TYPE, "project": STR, "summary": STR,
            "amount_before": STR, "amount_after": STR,
            "evidence": {"type": "array", "items": {"type": "object", "properties": {
                "doc_id": STR, "quote": STR, "what_it_shows": STR},
                "required": ["doc_id", "quote", "what_it_shows"], "additionalProperties": False}},
            "searched_for": STR, "news_values": NEWS, "why_it_surfaced": STR,
        }, "required": ["lead_id", "title", "lead_type", "project", "summary", "amount_before", "amount_after",
                        "evidence", "searched_for", "news_values", "why_it_surfaced"],
            "additionalProperties": False}},
        "dropped": {"type": "array", "items": {"type": "object", "properties": {"title": STR, "reason": STR},
                                               "required": ["title", "reason"], "additionalProperties": False}},
    }),
    "Skeptic": _tool("submit_verdicts", "Hand your verdict on every lead back to the app.", {
        "verdicts": {"type": "array", "items": {"type": "object", "properties": {
            "lead_id": STR, "verdict": {"type": "string", "enum": ["keep", "kill"]}, "reason": STR,
            "alternative_explanation": STR, "next_steps": {"type": "array", "items": STR},
            "exception_news_value": STR, "exception_doc_id": STR, "exception_quote": STR,
        }, "required": ["lead_id", "verdict", "reason", "alternative_explanation", "next_steps",
                        "exception_news_value", "exception_doc_id", "exception_quote"],
            "additionalProperties": False}},
    }),
}

AGENT_PROMPT_FILES = {"Scout": "scout.md", "Connector": "connector.md", "Skeptic": "skeptic.md"}


# ---------------------------------------------------------------- prompts

def system_prompt(agent: str, store: DocumentStore) -> str:
    """Stable parts first (same for every run and every agent) so the provider can cache them."""
    index = "\n".join(f"- {d['doc_id']} | {d['type']} | {d['date']} | {d['pages']} page(s)"
                      + (" | ADDED BY JOURNALIST" if d["added_by_journalist"] else "")
                      for d in tools.list_documents(store)["documents"])
    return "\n\n".join([
        (PROMPTS / "common.md").read_text(),
        (PROMPTS / "news_values.md").read_text(),
        f"# Collection notes\n\n{store.notes}",
        f"# Document index ({len(store.docs)} documents)\n\n{index}",
        (PROMPTS / AGENT_PROMPT_FILES[agent]).read_text(),
    ])


# ---------------------------------------------------------------- the agent loop

@dataclass
class RunContext:
    llm: LLM
    store: DocumentStore
    counter: ToolCallCounter
    trace: Trace
    on_progress: callable = field(default=lambda message: None)


def _summarize(name: str, result: dict) -> str:
    """One line for the trace, so it stays readable."""
    if "error" in result:
        return f"error: {result['error']}"
    return {
        "list_documents": lambda r: f"{len(r['documents'])} documents",
        "search_documents": lambda r: f"{r['total_matches']} matches",
        "read_section": lambda r: f"read {r['doc_id']} page {r['page']}",
        "lookup_project": lambda r: f"mentioned in {len(r['documents_mentioning'])} documents",
        "compare_passages": lambda r: (f"{r['change']['from']:,.0f} -> {r['change']['to']:,.0f} "
                                       f"({r['change']['percent']}%)" if isinstance(r["change"], dict) else r["change"]),
        "fetch_passage": lambda r: f"found on page {r['page']}" if r.get("found") else "not found",
    }[name](result)


def run_agent(ctx: RunContext, agent: str, task: str, tool_names: list[str]) -> dict:
    submit = SUBMIT[agent]
    submit_name = submit["function"]["name"]
    schemas = [TOOL_SCHEMAS[n] for n in tool_names] + [submit]
    messages = [{"role": "system", "content": system_prompt(agent, ctx.store)},
                {"role": "user", "content": task}]
    must_submit = False

    for _ in range(ctx.counter.per_agent + 3):  # a backstop on top of the tool-call counter
        choice = {"type": "function", "function": {"name": submit_name}} if must_submit else None
        response = ctx.llm.call(agent, messages, tools=schemas, tool_choice=choice)
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:  # the model answered in text: ask it to hand off properly
            messages.append({"role": "user", "content": f"Call {submit_name} now to hand off your results."})
            must_submit = True
            continue

        handoff = None
        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            if call.function.name == submit_name:
                handoff, result = args, {"ok": True}
            else:
                try:
                    ctx.counter.record(agent)
                    result = tools.TOOLS[call.function.name](ctx.store, **args)
                except ToolLimitReached as stop:
                    result = {"error": f"{stop} Submit your results now with what you have."}
                    must_submit = True
                    ctx.trace.add(agent, "stop", str(stop))
                except (KeyError, TypeError) as problem:
                    result = {"error": f"Bad tool call: {problem}"}
                ctx.trace.add(agent, "tool_call", f"{call.function.name}({_short(args)}) → {_summarize(call.function.name, result)}",
                              {"tool": call.function.name, "args": args})
                ctx.on_progress(f"{agent}: {call.function.name}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})

        if handoff is not None:
            return handoff
    raise AgentError(f"{agent} did not hand off its results.")


def _short(args: dict) -> str:
    return ", ".join(f"{k}={str(v)[:60]!r}" for k, v in args.items())
