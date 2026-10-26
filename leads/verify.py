"""Plain-code check that every evidence quote really appears in its source file.

Rule (agreed with the journalist): before comparing,
  - any run of spaces, tabs, or line breaks counts as one space, and
  - curly and straight quote marks count as the same (’ = ', “ = ").
Everything else — every word, number, dollar sign, and punctuation mark — must match exactly.
"""

from . import config
from .documents import DocumentStore

QUOTE_MARKS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def normalize(text: str) -> str:
    return " ".join(text.translate(QUOTE_MARKS).split())


def quote_in_text(quote: str, text: str) -> bool:
    quote = normalize(quote)
    return bool(quote) and quote in normalize(text)


def check_quote(store: DocumentStore, doc_id: str, quote: str) -> tuple[bool, str]:
    """Return (verified, reason)."""
    doc = store.get(doc_id)
    if doc is None:
        return False, f"No document named '{doc_id}' in the collection."
    if len(normalize(quote)) < config.MIN_QUOTE_CHARS:
        return False, f"Quote is shorter than {config.MIN_QUOTE_CHARS} characters, too short to verify."
    if not quote_in_text(quote, doc.full_text):
        return False, "Quote does not appear word-for-word in the source file."
    return True, "Quote found word-for-word in the source file."


def verify_lead(store: DocumentStore, lead: dict) -> dict:
    """Mark each evidence item as verified or not, and the lead as a whole.

    A lead with any unverified quote is flagged so the app can drop it.
    """
    all_ok = bool(lead.get("evidence"))
    for item in lead.get("evidence", []):
        ok, reason = check_quote(store, item.get("doc_id", ""), item.get("quote", ""))
        item["verified"] = ok
        item["verification_note"] = reason
        all_ok = all_ok and ok
    lead["all_evidence_verified"] = all_ok
    return lead
