"""Recent news coverage for a beat: headlines only, from Google News' public search feed.

Plain code, no AI: headlines are never sent to the model, so they can't steer it and cost no tokens.
Used to show what's already being reported on a beat, and to mark leads that may already be covered.
"""

import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import certifi

FEED = "https://news.google.com/rss/search?"
DAYS = 30
BEAT_QUERIES = {
    "Public spending": '"Beaufort County" (budget OR spending OR contract OR "change order" OR overrun)',
    "Growth & development": '"Beaufort County" (development OR construction OR growth OR rezoning OR building)',
    "Local government": '"Beaufort County Council" OR "Beaufort County" (council OR administrator OR vote)',
    "Education": '"Beaufort County School District" OR "Beaufort County" (schools OR "school board")',
    "Environment & climate": '"Beaufort County" (flooding OR stormwater OR environment OR conservation OR climate)',
    "Transportation": '"Beaufort County" (road OR traffic OR "sales tax" OR bridge OR airport)',
    "Housing": '"Beaufort County" (housing OR "affordable housing" OR "workforce housing")',
    "Public safety": '"Beaufort County" (sheriff OR arrest OR jail OR EMS OR "fire station")',
    "Events, openings & closings": '("Hilton Head" OR Beaufort OR Bluffton OR "Port Royal") (festival OR parade OR '
                                   '"grand opening" OR "ribbon cutting" OR concert)',  # crime headlines are dropped in code
}
SC_PLACES = '(SC OR "South Carolina" OR Bluffton OR "Hilton Head" OR "Port Royal" OR "Lady\'s Island")'
# There is also a Beaufort County in North Carolina, so only South Carolina outlets are kept.
SC_OUTLETS = ("island packet", "beaufort gazette", "the state", "post and courier", "island news", "wtoc",
              "wsav", "wjcl", "sc daily gazette", "south carolina daily gazette", "bluffton", "hilton head",
              "lowcountry", "live 5", "wcsc", "wcbd", "count on 2", "scetv", "south carolina public radio",
              "sc public radio", "the nerve", "beaufort county", "port royal")
GENERIC = {"beaufort", "county", "project", "projects", "building", "office", "station", "road", "roads", "the",
           "and", "for", "improvements", "renovation", "construction", "new", "addition", "site", "development",
           "center", "phase", "park", "pool", "resurfacing", "tracker", "cost", "county's"}


# Crime and death stories never count as coverage on these beats, even if a word like "closed" matched.
CRIME = re.compile(r"\b(homicide|murder\w*|shoot\w*|shot|kill\w*|dead|death\w*|died|dies|stabb\w*|arrest\w*|"
                   r"charged|suspect\w*|crash\w*|fatal\w*|body|bodies|police|sheriff|deputies|investigat\w*)\b",
                   re.IGNORECASE)
NO_CRIME_BEATS = {"Events, openings & closings", "Education", "Housing", "Environment & climate"}


class CoverageUnavailable(Exception):
    """The news feed could not be reached or read."""


def fetch_coverage(beat: str, limit: int = 10, timeout: int = 15) -> list[dict]:
    """Headlines from the last 30 days for this beat, newest first."""
    terms = BEAT_QUERIES.get(beat, '"Beaufort County"')
    if beat == "Events, openings & closings":  # already names local places; Google returns nothing if it's wrapped
        query = f"{terms} when:{DAYS}d"
    else:
        query = f"({terms}) {SC_PLACES} when:{DAYS}d"
    url = FEED + urllib.parse.urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Scout newsroom tool)"})
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            items = parse_feed(response.read(), limit=100)
    except (urllib.error.URLError, TimeoutError, OSError, ET.ParseError):
        raise CoverageUnavailable("Recent news coverage couldn't be loaded right now, so leads weren't checked "
                                  "against it. Everything else on this page is unaffected.")
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)  # Google sometimes ignores "when:30d"
    items = [i for i in items if any(o in i["source"].lower() for o in SC_OUTLETS) and i["date"] >= cutoff]
    if beat in NO_CRIME_BEATS:
        items = [i for i in items if not CRIME.search(i["title"])]
    seen, unique = set(), []
    for i in items:  # the same story is sometimes listed twice
        key = re.sub(r"\W+", " ", i["title"].lower()).strip()
        if key not in seen:
            seen.add(key)
            unique.append(i)
    return unique[:limit]


def parse_feed(data: bytes, limit: int = 10) -> list[dict]:
    items = []
    for item in ET.fromstring(data).findall("./channel/item"):
        source = item.findtext("source") or ""
        title = item.findtext("title") or ""
        if source and title.endswith(f" - {source}"):  # Google appends the outlet to the headline
            title = title[: -len(source) - 3]
        try:
            date = parsedate_to_datetime(item.findtext("pubDate"))
        except (TypeError, ValueError):
            continue
        items.append({"title": title, "source": source, "url": item.findtext("link") or "", "date": date})
    items.sort(key=lambda i: i["date"], reverse=True)
    seen, unique = set(), []
    for i in items:  # the same story is sometimes listed twice
        key = re.sub(r"\W+", " ", i["title"].lower()).strip()
        if key not in seen:
            seen.add(key)
            unique.append(i)
    return unique[:limit]


def distinctive_words(name: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9#']+", name.lower()) if len(w) > 2 and w not in GENERIC]


def overlapping(project: str, items: list[dict]) -> list[dict]:
    """Recent headlines that mention every distinctive word of a project's name."""
    words = distinctive_words(project)
    if not words:
        return []
    return [i for i in items if all(re.search(rf"\b{re.escape(w)}\b", i["title"].lower()) for w in words)]
