"""Events beat: the three calendar formats are read in code, and routine meetings are dropped."""

import json
from datetime import datetime

from leads import events

TODAY = datetime(2026, 10, 25)
ICS = b"""BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20261111T000000
SUMMARY:County Offices Closed
LOCATION:Beaufort\\, SC
END:VEVENT
BEGIN:VEVENT
DTSTART:20261102T100000
SUMMARY:Natural Resources Committee (T)
END:VEVENT
BEGIN:VEVENT
DTSTART:20250101T100000
SUMMARY:Old event last year
END:VEVENT
END:VCALENDAR"""
HHI = json.dumps([{"title": "Hilton Head Oyster Festival", "start": "2026-11-06T11:00:00", "location": "",
                   "primary_calendar_name": "Special Event Permits", "url": "https://example.com/oyster"},
                  {"title": "Town Council Workshop - CANCELLED", "start": "2026-10-27T10:00:00",
                   "primary_calendar_name": "Public Meetings"},
                  {"title": "Board of Zoning Appeals", "start": "2026-10-26T14:00:00",
                   "primary_calendar_name": "Public Meetings"}]).encode()
RSS = b"""<rss><channel><item><title>Trunk or Treat</title><link>https://example.com/trunk</link>
<description>Event date: October 30, 2026 Event Time: 03:00 PM Location: Historic Downtown Port Royal</description>
</item></channel></rss>"""


def titles(found):
    return [e["title"] for e in found if events.keep(e, TODAY)]


def test_county_calendar_keeps_closings_and_drops_meetings_and_old_events():
    assert titles(events.beaufort_county(ICS)) == ["County Offices Closed"]


def test_hilton_head_keeps_festivals_and_cancellations_but_not_routine_meetings():
    assert titles(events.hilton_head(HHI)) == ["Hilton Head Oyster Festival"]  # cancelled meeting is routine


def test_port_royal_feed_is_read():
    found = events.port_royal(RSS)
    assert titles(found) == ["Trunk or Treat"] and found[0]["where"].startswith("Historic Downtown")


def test_events_become_one_quotable_document(monkeypatch):
    feeds = {events.SOURCES["Beaufort County"]: ICS, events.SOURCES["Town of Hilton Head Island"]: HHI,
             events.SOURCES["Town of Port Royal"]: RSS}
    monkeypatch.setattr(events, "_get", lambda url: feeds[url])
    name, data, summary = events.fetch_events(TODAY)
    text = data.decode()
    assert name == "event_calendars_2026-10-25.txt" and summary["failed"] == []
    assert "Event: Hilton Head Oyster Festival | Date: Friday, November 06, 2026" in text
    assert "Board of Zoning Appeals" not in text
