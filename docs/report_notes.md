# Submission rules (from the professor, Oct. 25)

Canvas accepts **files only** (no URL field). Submit exactly:
1. `report.html` — must include the **GitHub repo URL** so graders can clone it
2. `slides.html` — must also include the **GitHub repo URL**
3. A demo video (optional)

**Nothing else**: any other files are penalized. If the repo is **private**, say so in both the report and the
slides (and add GitHub user `zlisto` as a collaborator so they can clone it).

# Notes for the report (working file)

## Limits + next steps (section 8)

- **Social Media Monitor.** Scan Facebook, Instagram, X, and other platforms for people talking about
  Hilton Head, Beaufort County, and local events, by beat, using hashtags and keywords.
  - Why it isn't built yet: tested 2026-10-25. Facebook and Instagram show login walls, X serves an
    empty page that needs a logged-in browser, and Reddit and Bluesky returned 403 "Blocked/Forbidden".
    Reading them automatically needs paid or approved developer accounts and new API keys, which the
    course allows only if the app is hosted online and the professor approves. Scraping behind login
    walls breaks the platforms' terms of service.
  - Planned design: one-click, beat-specific hashtag searches that open in the reporter's own logged-in
    browser, plus a "paste posts" box. An agent compares pasted posts with the beat's leads. Posts count
    as tips, never as verified evidence, and private individuals are never named on a card.
- **Move the built-in county records to the current year.** The county stopped publishing dated project
  lists (now an interactive dashboard), so "numbers changed" leads for current projects need saved
  snapshots of that dashboard over time. The past year's Council and committee minutes are already
  available as a one-click set.
- **"What's new since my last scan."** Remember past results and flag new leads each week.
- **Records-request drafter.** One click turns a lead into a South Carolina FOIA request that names the
  exact documents and figures.
- **Arrest records.** Currently only from a reporter-uploaded or fetched jail log, with privacy fields
  removed in code. Future: human review before any arrest card is shown, and a check for later charge
  outcomes (dropped, reduced, dismissed).

## Changes from the original plan (be upfront about these)

- A third lead type, **"Worth a closer look"** (conflict, split votes, sole-source or emergency
  contracts, officials saying they weren't told), was added because reporters want stories, not
  paperwork. Routine "no approval found" items are now filtered out by the Skeptic.
- **Arrest records** were added at the reporter's request, only from an uploaded or fetched jail log,
  with code-level safeguards.
- Optional live features: **Check the jail log** and **recent news coverage**. Everything else runs from
  the shipped files.
- **Jail-log flags are applied in plain code** (`leads/jail.py`), using the newsroom's list agreed with
  the reporter: serious or violent charges, children involved, 28 g or more of drugs,
  ICE holds counted as a pattern (never named), and names that also appear in the public records
  ("identity not confirmed"). Why: in a live test the AI spotted these bookings but was too cautious to
  submit them. The agents then check each flagged booking. Example from 2026-10-25: code flagged three
  "28 grams or less" marijuana bookings as trafficking, the Connector set them aside, and the rule was
  fixed. This is a good example of the multi-agent double-check catching a code bug.
- When a jail log is added, the results page always reports what happened, e.g. "Jail log checked:
  Scout read all 37 bookings and flagged 4 below," or "...found nothing newsworthy."
- **"Events, openings & closings" replaced "Public spending" as a beat** because spending already runs
  through every other beat. Public spending remains the "See an example" search and the evaluation's beat
  (the hand-checked reference leads are spending stories). Calendars: Beaufort County (ICS file), Hilton Head
  Island (Revize calendar data), Port Royal (RSS feed). Code drops routine meetings; the agents pick the
  fun or newsworthy items. First live test: the Scout refused to quote a calendar page that was cut off,
  so the list is now split into 20-event pages.
- **Beat cards show Scout holding each beat's emoji** (drawn by `scripts/make_beat_art.py`).
- **"So what" is used to decide but is never shown as a tag.**
- **"Who to contact" on every card:** public officials named in the lead are matched (in code) to official
  contact info from government websites, plus the offices for the beat. Private individuals never get
  contact details, including anyone in a jail log. Arrest cards point to the Sheriff's and Solicitor's offices.
