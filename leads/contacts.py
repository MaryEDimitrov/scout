"""Who a reporter could call about a lead: public officials named in it, plus the offices for the beat.

Contact details come only from data/contacts.json, which was copied from government websites
(each entry keeps its source link). Public officials and offices only: never private individuals,
and never anyone named in a jail log.
"""

import json
import re
from functools import lru_cache

from . import config

TITLES = (r"(?:Council\s?Member|Councilm[ae]n|Councilwoman|Committee Chairman|Committee Chair|Committee Vice[- ]Chair|"
          r"Vice[- ]Chairman|Vice[- ]Chair|Chairman|Chairwoman|Chair|Mayor Pro[- ]Tem|Mayor|Mr\.|Ms\.|Mrs\.|Dr\.)")
BEAT_OFFICES = {
    "Events, openings & closings": ["hhi_town_hall", "port_royal", "county_pio"],
    "Growth & development": ["county_pio", "county_admin"],
    "Local government": ["county_pio", "county_admin", "hhi_town_hall"],
    "Education": ["school_district"],
    "Environment & climate": ["county_pio", "county_admin"],
    "Transportation": ["county_pio", "county_admin"],
    "Housing": ["county_pio", "hhi_town_hall"],
    "Public safety": ["sheriff", "solicitor", "county_pio"],
    "Public spending": ["county_pio", "county_admin"],
}


@lru_cache(maxsize=1)
def directory() -> dict:
    return json.loads((config.PROJECT_DIR / "data" / "contacts.json").read_text(encoding="utf-8"))


def _named(person: dict, text: str) -> bool:
    names = [person["name"], *person.get("aliases", [])]
    if any(re.search(rf"\b{re.escape(n)}\b", text) for n in names):
        return True
    return bool(re.search(rf"\b{TITLES}\s+{re.escape(person['last_name'])}\b", text))


def contacts_for(card: dict, beat: str) -> dict:
    """{"people": [...], "offices": [...]} for one lead card."""
    offices = [directory()["offices"][k] for k in BEAT_OFFICES.get(beat, ["county_pio"])]
    if card["lead_type"] == "Arrest record":  # never contact details for anyone in a jail log
        return {"people": [], "offices": [directory()["offices"][k] for k in ("sheriff", "solicitor", "county_pio")]}

    text = " ".join([card["title"], card["lead"], *[e["quote"] for e in card["evidence"]]])
    files = " ".join(e["file"].lower() for e in card["evidence"])
    body = "Town of Hilton Head Island" if "hhi" in files else "Beaufort County"
    people = [p for p in directory()["people"] if _named(p, text)]
    # Two officials can share a surname (a county Brown and a Hilton Head Brown): keep the one from
    # the government whose records the lead quotes, unless the full name was written out.
    surnames = [p["last_name"] for p in people]
    people = [p for p in people if surnames.count(p["last_name"]) == 1 or p["body"] == body
              or re.search(rf"\b{re.escape(p['name'])}\b", text)]
    return {"people": people, "offices": offices}
