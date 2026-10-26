"""Recent coverage: headlines are parsed in code and matched to leads by distinctive words."""

import pytest

from leads import coverage

FEED = b"""<?xml version="1.0"?><rss><channel>
<item><title>Arthur Horne building overrun questioned by council - Island Packet</title>
  <link>https://example.com/a</link><pubDate>Tue, 20 Oct 2026 10:00:00 GMT</pubDate><source>Island Packet</source></item>
<item><title>County hires new finance chief - Post and Courier</title>
  <link>https://example.com/b</link><pubDate>Thu, 22 Oct 2026 10:00:00 GMT</pubDate><source>Post and Courier</source></item>
</channel></rss>"""


def test_feed_is_parsed_newest_first_with_outlet_removed_from_headline():
    items = coverage.parse_feed(FEED)
    assert [i["source"] for i in items] == ["Post and Courier", "Island Packet"]
    assert items[1]["title"] == "Arthur Horne building overrun questioned by council"


def test_lead_is_matched_to_coverage_by_its_distinctive_words():
    items = coverage.parse_feed(FEED)
    assert [i["source"] for i in coverage.overlapping("Arthur Horne Office Building", items)] == ["Island Packet"]
    assert coverage.overlapping("EMS Station 31", items) == []


def test_generic_project_names_never_match_everything():
    assert coverage.overlapping("Beaufort County Building Project", coverage.parse_feed(FEED)) == []


def test_unreachable_feed_gives_a_plain_message(monkeypatch):
    def offline(*args, **kwargs):
        raise coverage.urllib.error.URLError("no network")
    monkeypatch.setattr(coverage.urllib.request, "urlopen", offline)
    with pytest.raises(coverage.CoverageUnavailable, match="couldn't be loaded"):
        coverage.fetch_coverage("Housing")


def test_events_coverage_never_includes_crime_stories(monkeypatch):
    import io
    feed = b"""<?xml version="1.0"?><rss><channel>
<item><title>Homicide investigation closes road on Hilton Head - Island Packet</title><link>a</link>
  <pubDate>Tue, 20 Oct 2026 10:00:00 GMT</pubDate><source>Island Packet</source></item>
<item><title>Oyster Festival returns to Hilton Head - Island Packet</title><link>b</link>
  <pubDate>Wed, 21 Oct 2026 10:00:00 GMT</pubDate><source>Island Packet</source></item>
</channel></rss>"""
    monkeypatch.setattr(coverage.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(feed))
    titles = [i["title"] for i in coverage.fetch_coverage("Events, openings & closings")]
    assert titles == ["Oyster Festival returns to Hilton Head"]
    assert len(coverage.fetch_coverage("Public safety")) == 2  # crime coverage stays on Public safety


def test_coverage_older_than_30_days_is_dropped(monkeypatch):
    import io
    from datetime import datetime, timedelta, timezone
    old = (datetime.now(timezone.utc) - timedelta(days=200)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    new = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    feed = f"""<?xml version="1.0"?><rss><channel>
<item><title>St. Patrick's Day parade guide - Island Packet</title><link>a</link><pubDate>{old}</pubDate><source>Island Packet</source></item>
<item><title>Lantern parade returns - WJCL</title><link>b</link><pubDate>{new}</pubDate><source>WJCL</source></item>
</channel></rss>""".encode()
    monkeypatch.setattr(coverage.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(feed))
    assert [i["title"] for i in coverage.fetch_coverage("Events, openings & closings")] == ["Lantern parade returns"]
