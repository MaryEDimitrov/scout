"""Apply the newsroom's arrest list to a jail log, in plain code.

The AI was too cautious to flag bookings on its own, so code does the matching: every booking line
is checked against the list below, and every booked name is looked up in the public records. Each
match becomes a candidate for the Connector and Skeptic, quoted exactly from the log.
"""

import re

from .documents import DocumentStore, name_pattern

# The newsroom's list (agreed with the reporter). Routine bookings match none of these.
FLAG_RULES = [
    ("Violent or serious charge", r"murder|homicide|manslaughter|assault (?:&|and) battery (?:of a )?high|"
                                  r"assault (?:&|and) battery,? (?:1st|2nd|first|second)|"
                                  r"domestic violence (?:of a )?high|domestic violence,? (?:1st|2nd|first|second)|"
                                  r"criminal sexual|sexual (?:assault|battery|conduct)|kidnap|armed robbery|"
                                  r"weapon|firearm|pistol|gun"),
    ("Child involved", r"child|minor|juvenile"),
    # "28 grams or more" (or trafficking) only; "28 grams or less" is simple possession
    ("Trafficking-level drugs", r"traffick|\b(?:28|100|200|400)\s?(?:g|grams?)\.?\s+or\s+more|more than 28\s?(?:g|grams?)"),
]
ICE = re.compile(r"\bICE hold\b", re.IGNORECASE)
BOOKING = re.compile(r"^Booking .*\| Name: (?P<name>[^|]+?) \|.*Charges: (?P<charges>.*)$")


def roster_documents(store: DocumentStore) -> list:
    """Documents that are jail logs: their lines start with 'Booking ... | Name: ...'."""
    return [d for d in store.docs.values() if d.added and any(BOOKING.match(l) for p in d.pages for l in p.splitlines())]


def flag_bookings(store: DocumentStore) -> tuple[list[dict], dict]:
    """Return (candidates for the Connector, summary counts)."""
    candidates, ice_lines, checked = [], [], 0
    other_docs = [d for d in store.docs.values() if d not in roster_documents(store)]
    for doc in roster_documents(store):
        for page in doc.pages:
            for line in page.splitlines():
                m = BOOKING.match(line)
                if not m:
                    continue
                checked += 1
                reasons = [label for label, rule in FLAG_RULES if re.search(rule, m["charges"], re.IGNORECASE)]
                name = m["name"].strip()
                pattern = name_pattern(name)
                also_in = [d.source_file for d in other_docs if any(pattern.search(p) for p in d.pages)]
                if also_in:
                    reasons.append("Name also appears in " + ", ".join(also_in[:2]) + " (identity not confirmed)")
                if ICE.search(m["charges"]):
                    ice_lines.append((doc.doc_id, line))
                if reasons:
                    candidates.append({
                        "title": f"Booking flagged: {reasons[0].split(' (')[0].lower()}",
                        "lead_type": "arrest_record", "project": name,
                        "what_caught_my_eye": "Matches the newsroom's arrest list: " + "; ".join(reasons),
                        "news_values": ["Impact"], "pointers": [{"doc_id": doc.doc_id, "quote": line}],
                    })
    if len(ice_lines) >= 2:  # ICE holds are reported as a pattern, never by name
        candidates.append({
            "title": f"{len(ice_lines)} ICE holds in the jail log", "lead_type": "arrest_record",
            "project": "ICE holds",
            "what_caught_my_eye": f"{len(ice_lines)} bookings list an ICE hold. Report the count, not names.",
            "news_values": ["Currency", "Impact"],
            "pointers": [{"doc_id": d, "quote": "Charges: " + re.search(r"Charges: (.*)", l)[1]} for d, l in ice_lines[:3]],
        })
    return candidates, {"bookings_checked": checked, "flagged": len(candidates), "ice_holds": len(ice_lines)}
