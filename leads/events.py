"""Upcoming events from the Beaufort County, Hilton Head Island, and Port Royal calendars.

Fetched when a reporter searches the Events beat. Routine meetings are dropped here in code; what is
left (festivals, openings, closings, cancellations, community events) becomes one document that the
agents read like any other, so every event card quotes a real calendar line.
"""

import html
import json
import re
import ssl
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import certifi

DAYS_AHEAD = 45
SOURCES = {
    "Beaufort County": "https://beaufortcountysc.gov/events/calendar.ics",
    "Town of Hilton Head Island": ("https://hiltonheadislandsc.gov/_assets_/plugins/revizeCalendar/calendar_data_handler.php"
                                   "?webspace=hiltonhead&relative_revize_url=//cms1.revize.com&protocol=https:"),
    "Town of Port Royal": "https://www.portroyal.org/RSSFeed.aspx?ModID=58&CID=All-calendar.xml",
}
ROUTINE = re.compile(r"\b(meeting|committee|commission|board|caucus|council|session|workshop|appeals|authority|"
                     r"trustees|airports)\b", re.IGNORECASE)
KEEP_ANYWAY = re.compile(r"clos|open|grand|ribbon|festival|celebrat|parade|market|concert|fair\b|chat|cleanup|"
                         r"holiday", re.IGNORECASE)  # a cancelled routine meeting is still routine


class EventsUnavailable(Exception):
    """None of the calendars could be read."""


def _get(url: str, timeout: int = 20) -> bytes:
    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Scout newsroom tool)"})
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read()


def _clean(text: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text or "")).replace("\\,", ",").replace("\\n", " ").split())


def beaufort_county(data: bytes) -> list[dict]:
    text = data.decode("utf-8", "replace").replace("\r\n ", "").replace("\n ", "")
    events = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        def field(name):
            m = re.search(rf"^{name}[^:\n]*:(.*)$", block, re.M)
            return m.group(1).strip() if m else ""
        try:
            start = datetime.strptime(field("DTSTART")[:8], "%Y%m%d")
        except ValueError:
            continue
        events.append({"title": _clean(field("SUMMARY")), "start": start, "where": _clean(field("LOCATION")),
                       "calendar": "Beaufort County", "link": field("URL")})
    return events


def hilton_head(data: bytes) -> list[dict]:
    events = []
    for e in json.loads(data):
        try:
            start = datetime.fromisoformat(e["start"][:19])
        except (KeyError, ValueError):
            continue
        events.append({"title": _clean(e.get("title", "")), "start": start, "where": _clean(e.get("location", "")),
                       "calendar": f"Town of Hilton Head Island ({e.get('primary_calendar_name', '')})",
                       "link": e.get("url", "")})
    return events


def port_royal(data: bytes) -> list[dict]:
    events = []
    for item in ET.fromstring(data).findall("./channel/item"):
        desc = _clean(item.findtext("description") or "")
        m = re.search(r"Event date:\s*([A-Z][a-z]+ \d{1,2}, \d{4})", desc)
        if not m:
            continue
        where = re.search(r"Location:\s*(.*)", desc)
        events.append({"title": _clean(item.findtext("title")), "start": datetime.strptime(m.group(1), "%B %d, %Y"),
                       "where": where.group(1).strip() if where else "", "calendar": "Town of Port Royal",
                       "link": item.findtext("link") or ""})
    return events


PARSERS = {"Beaufort County": beaufort_county, "Town of Hilton Head Island": hilton_head, "Town of Port Royal": port_royal}


def keep(event: dict, today: datetime) -> bool:
    upcoming = today <= event["start"] <= today + timedelta(days=DAYS_AHEAD)
    routine = ROUTINE.search(event["title"]) and not KEEP_ANYWAY.search(event["title"])
    return bool(event["title"]) and upcoming and not routine


def fetch_events(today: datetime | None = None) -> tuple[str, bytes, dict]:
    """Return (file name, document text, summary) for the Events beat."""
    today = (today or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    events, summary = [], {"failed": []}
    for name, url in SOURCES.items():
        try:
            found = [e for e in PARSERS[name](_get(url)) if keep(e, today)]
            summary[name] = len(found)
            events += found
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, ET.ParseError):
            summary["failed"].append(name)
    if not events and summary["failed"]:
        raise EventsUnavailable("The event calendars couldn't be reached right now. Try again in a few minutes.")
    events.sort(key=lambda e: e["start"])
    lines = [f"Event: {e['title']} | Date: {e['start']:%A, %B %d, %Y} | Where: {e['where'] or 'not listed'} | "
             f"Calendar: {e['calendar']} | Link: {e['link'] or 'none'}" for e in events]
    # Short pages (20 events each) so an agent always reads whole calendar lines.
    pages = [f"=== Page {n} ===\n" + "\n".join(lines[i:i + 20]) for n, i in enumerate(range(0, len(lines), 20), 1)]
    header = (f"Upcoming events, openings, and closings from local government calendars, fetched {today:%B %d, %Y}. "
              "Routine public meetings were left out.\n")
    return f"event_calendars_{today:%Y-%m-%d}.txt", (header + "\n".join(pages)).encode("utf-8"), summary
