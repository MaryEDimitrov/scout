"""Scout: a step-by-step web app that helps a reporter find story leads in public records.

Run with:  streamlit run app.py

Steps:  1. pick a beat  ->  2. add documents (optional)  ->  3. read the story leads
"""

import base64
import html
import json
import re
from pathlib import Path

import streamlit as st

from leads import config
from leads.contacts import contacts_for
from leads.coverage import CoverageUnavailable, fetch_coverage, overlapping
from leads.documents import DocumentStore
from leads.pipeline import run_investigation
from leads.events import EventsUnavailable, fetch_events
from leads.uploads import FetchFailed, build_collection, extract_text, fetch_jail_roster

ASSETS = Path(__file__).parent / "assets"
EXAMPLE_BEAT = "Public spending"
BEATS = {  # icon and a plain-language description for each beat
    "Events, openings & closings": ("🎉", "Festivals, grand openings, closings, and cancellations across the county."),
    "Growth & development": ("🏗️", "Construction, new buildings, land, and how the county is growing."),
    "Local government": ("🏛️", "What Council approved, questioned, or was never told."),
    "Education": ("🎓", "School buildings, school board decisions, and libraries."),
    "Environment & climate": ("🌊", "Flooding, drainage, parks, and conservation land."),
    "Transportation": ("🚗", "Roads, paving, sidewalks, bridges, and airports."),
    "Housing": ("🏠", "Affordable and workforce housing, and land bought for housing."),
    "Public safety": ("🚔", "EMS and fire stations, the sheriff, the jail, and newsworthy arrests."),
}
BEAT_GUIDE = {  # what Scout looks for on each beat, and what a reporter could add (shown on step 2)
    "Events, openings & closings": ("fun events, grand openings, and closings on the county, Hilton Head, and Port "
                                    "Royal calendars",
                                    "event flyers, press releases, or a business's opening announcement"),
    "Public spending": ("cost jumps, unapproved spending, and hidden overruns",
                        "budget amendments, finance committee minutes, contracts, or change orders"),
    "Growth & development": ("construction projects that changed or moved without approval",
                             "planning commission or zoning board minutes, or development agreements"),
    "Local government": ("what Council approved, questioned, or wasn't told",
                         "minutes or agendas from town councils or county committees"),
    "Education": ("school projects and spending that changed or lack approval",
                  "Beaufort County School District board minutes, agendas, or budget documents"),
    "Environment & climate": ("flooding, stormwater, and conservation projects that changed",
                              "stormwater board, natural resources committee, or Rural and Critical Lands minutes"),
    "Transportation": ("road, sidewalk, and bridge projects that changed or lack approval",
                       "transportation committee minutes or sales-tax project updates"),
    "Housing": ("housing spending and land bought for housing",
                "housing authority or town council minutes about housing"),
    "Public safety": ("EMS, fire, sheriff, and jail spending, plus newsworthy arrests",
                      "public safety committee minutes, or today's jail log (button below)"),
}
LEAD_TYPES = {"Change": "The numbers changed", "Missing link": "No approval found",
              "Worth a closer look": "Worth a closer look", "Event": "Event", "Opening or closing": "Opening or closing",
              "Arrest record": "Arrest record"}
PROGRESS = {0.1: "Reading the records…", 0.4: "Connecting the dots across documents…",
            0.7: "Double-checking each lead…", 0.9: "Checking every quote against the original files…"}

st.set_page_config(page_title="Scout · Beaufort County Records Desk", page_icon="🐊", layout="centered",
                   initial_sidebar_state="collapsed")


def image(name: str, width: int, label: str) -> str:
    data = base64.b64encode((ASSETS / name).read_bytes()).decode()
    return f'<img src="data:image/svg+xml;base64,{data}" width="{width}" alt="{label}">'


def beat_art(beat: str, width: int) -> str:
    """Scout holding the beat's emoji (assets/beats/, drawn by scripts/make_beat_art.py)."""
    slug = re.sub(r"[^a-z0-9]+", "-", beat.lower()).strip("-")
    path = ASSETS / "beats" / f"{slug}.svg"
    return image(f"beats/{slug}.svg", width, f"Scout holding the {beat} sign") if path.exists() else ""


def esc(text) -> str:
    """Everything the AI wrote is shown as plain text, never as HTML."""
    return html.escape(str(text or ""))


st.html("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap');
  :root { --ink: #121212; --muted: #5F5F5F; --rule: #D9D9D9; --accent: #A6192E; --tint: #F6F6F4; }
  html, body, [class*="css"], .stMarkdown, button, input, label, p { font-family: 'Libre Franklin', Arial, sans-serif; color: var(--ink); }
  .block-container { padding-top: 3.2rem; max-width: 780px; }

  .masthead { text-align: center; border-bottom: 3px double var(--ink); padding-bottom: .6rem; margin-bottom: .9rem; }
  .masthead .topline { font-size: .7rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--muted);
                       border-top: 1px solid var(--ink); border-bottom: 1px solid var(--rule); padding: .3rem 0; margin-bottom: .4rem; }
  .masthead .brand { display: flex; align-items: center; justify-content: center; gap: .4rem; }
  .masthead h1 { font-family: 'Source Serif 4', Georgia, serif; font-weight: 700; font-size: 3rem; letter-spacing: -.02em;
                 margin: 0; line-height: 1; color: var(--ink); }
  .masthead .tagline { font-family: 'Source Serif 4', Georgia, serif; font-style: italic; color: var(--muted); font-size: 1rem; }

  .steps { display: flex; justify-content: center; gap: .4rem; margin: .2rem 0 1.2rem; font-size: .72rem; font-weight: 700;
           letter-spacing: .1em; text-transform: uppercase; color: #9A9A9A; }
  .steps .on { color: var(--accent); } .steps .done { color: var(--ink); } .steps .sep { color: var(--rule); }
  .ask { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.9rem; font-weight: 700; line-height: 1.15; margin: 0 0 .3rem; }
  .sub { color: #444; font-size: .97rem; line-height: 1.55; margin-bottom: 1rem; }

  .beat-art { height: 132px; display: flex; align-items: flex-end; justify-content: center; margin: 0 0 .5rem; }
  .beat-art img { height: 100%; width: auto; }
  .ask-row img { height: 92px; width: auto; }
  .ask-row { display: flex; align-items: center; gap: .8rem; }
  .beat { font-size: 1.05rem; font-weight: 700; margin-bottom: .1rem; }
  .beat-desc { color: var(--muted); font-size: .86rem; line-height: 1.45; min-height: 2.6em; }

  .card { border-top: 1px solid var(--ink); padding: 1rem 0 1.3rem; margin: 0 0 .4rem; }
  .kicker { font-size: .7rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); }
  .kicker .values { color: var(--muted); font-weight: 600; }
  .card h3 { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.5rem; font-weight: 700; line-height: 1.2;
             margin: .3rem 0 .55rem; color: var(--ink); letter-spacing: -.01em; }
  .dek { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.05rem; line-height: 1.55; color: #262626; }
  .label { font-size: .68rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: var(--ink);
           margin: 1.05rem 0 .3rem; padding-bottom: .2rem; border-bottom: 1px solid var(--rule); }
  .text { font-size: .93rem; line-height: 1.6; color: #262626; }
  .quote { border-left: 3px solid var(--accent); padding: .15rem 0 .15rem .9rem; margin: .65rem 0; }
  .quote .q { font-family: 'Source Serif 4', Georgia, serif; font-size: 1rem; line-height: 1.5; color: var(--ink); }
  .quote .file { display: block; font-size: .7rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
                 color: var(--muted); margin-bottom: .2rem; }
  .quote .note { display: block; font-size: .8rem; color: var(--muted); margin-top: .25rem; }
  .notice { margin-top: 1rem; font-size: .85rem; background: #FBEDEF; border-left: 3px solid var(--accent);
            padding: .55rem .75rem; color: #5A0F1B; }
  .nv { display: flex; flex-wrap: wrap; align-items: center; gap: .35rem; margin: .1rem 0 .7rem; }
  .nv-label { font-size: .66rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: var(--muted);
              margin-right: .2rem; }
  .chip { font-size: .74rem; font-weight: 700; padding: .2rem .55rem; border-radius: 3px; }
  .money { display: flex; flex-wrap: wrap; align-items: baseline; gap: .55rem; margin: .1rem 0 .6rem;
           font-family: 'Source Serif 4', Georgia, serif; font-size: 1.45rem; font-weight: 700; }
  .money .arrow { color: var(--muted); font-weight: 400; }
  .money .delta { font-family: 'Libre Franklin', Arial, sans-serif; font-size: .85rem; font-weight: 800;
                  color: var(--accent); background: #FBEDEF; padding: .15rem .45rem; border-radius: 3px; }
  .tags { margin: .6rem 0 .2rem; }
  .tag { display: inline-block; font-size: .78rem; color: var(--muted); background: var(--tint); padding: .2rem .55rem;
         border-radius: 3px; }
  .tag.hot { color: #1B3550; background: #EEF3F8; }
  .tag a { color: inherit; }
  .folds { margin-top: .7rem; border-top: 1px solid var(--rule); }
  .card details { border-bottom: 1px solid var(--rule); }
  .card summary { cursor: pointer; padding: .55rem 0; font-size: .78rem; font-weight: 800; letter-spacing: .08em;
            text-transform: uppercase; color: var(--ink); list-style: none; }
  .card summary::-webkit-details-marker { display: none; }
  .card summary::before { content: "+"; display: inline-block; width: 1.1rem; color: var(--accent); font-weight: 800; }
  .card details[open] summary::before { content: "–"; }
  .fold { padding: 0 0 .8rem 1.1rem; font-size: .92rem; line-height: 1.6; color: #262626; }
  .fold ul { margin: .1rem 0 0 1rem; padding: 0; } .fold .why { margin: .5rem 0 0; }
  details.section { border-top: 2px solid var(--ink); border-bottom: 1px solid var(--rule); margin: 1.4rem 0 0; }
  details.section summary { display: flex; align-items: center; gap: 1rem; padding: .7rem 0; cursor: pointer;
                            list-style: none; }
  details.section summary::-webkit-details-marker { display: none; }
  details.section summary img { flex: none; }
  .sec-text { display: flex; flex-direction: column; flex: 1; }
  .sec-title { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.3rem; font-weight: 700; color: var(--ink); }
  .sec-sub { font-size: .85rem; color: var(--muted); margin-top: .1rem; }
  .sec-open { font-size: .7rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: var(--accent);
              border: 1px solid var(--accent); padding: .3rem .6rem; border-radius: 2px; }
  .sec-open::before { content: "Open"; }
  details.section[open] .sec-open { color: #fff; background: var(--accent); }
  details.section[open] .sec-open::before { content: "Close"; }
  .sec-body { padding: 0 0 1rem; }
  .sec-body .item { border-top: 1px solid var(--rule); padding: .65rem 0; }
  .sec-body .item a { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.02rem; font-weight: 600; color: var(--ink); }
  .sec-body .item b { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.02rem; }
  .sec-body .meta { font-size: .8rem; color: var(--muted); margin-top: .15rem; }
  .sec-body .meta.why { font-size: .88rem; color: #333; line-height: 1.5; }
  .who-head { font-size: .66rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: var(--muted);
              margin: .4rem 0 .2rem; }
  .who { padding: .35rem 0; border-bottom: 1px dotted var(--rule); }
  .who-links { font-size: .85rem; margin-top: .1rem; } .who-links a { color: var(--accent); }
  .who-note { font-size: .78rem; color: var(--muted); margin-top: .35rem; font-style: italic; }
  .covered { margin-top: 1rem; font-size: .85rem; background: #EEF3F8; border-left: 3px solid #2E5A88;
             padding: .55rem .75rem; color: #1B3550; }
  .covered b { letter-spacing: .08em; text-transform: uppercase; font-size: .7rem; }
  .covered a, .setaside a { color: inherit; }
  .confidence { margin-top: .6rem; font-size: .8rem; background: var(--tint); border-left: 3px solid var(--ink); padding: .5rem .75rem; }
  .notice b, .confidence b { letter-spacing: .08em; text-transform: uppercase; font-size: .7rem; }
  .setaside { border-top: 1px solid var(--rule); padding: .6rem 0; }
  .setaside b { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.02rem; }
  .loader { display: flex; flex-direction: column; align-items: center; padding: 1.4rem 0 .4rem; }
  .loader .cap { font-family: 'Source Serif 4', Georgia, serif; font-style: italic; color: #444; font-size: 1.1rem; margin-top: .3rem; }
  .footer { color: var(--muted); font-size: .78rem; margin-top: 2.2rem; text-align: center;
            border-top: 1px solid var(--rule); padding-top: .8rem; font-style: italic; }

  .stButton button { border-radius: 2px; font-weight: 700; letter-spacing: .02em; }
  .stButton button[kind="primary"] p { color: #FFFFFF; }
  div[data-testid="stAlert"] { border-radius: 2px; }
  section[data-testid="stFileUploaderDropzone"] { border: 1.5px dashed #9E9E9E; border-radius: 2px;
                                                 background: var(--tint); padding: 1.3rem; }
  section[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent); }
</style>
""")

st.html(f"""
<div class="masthead">
  <div class="topline">Beaufort County, S.C. &nbsp;·&nbsp; Public Records Desk</div>
  <div class="brand">{image("scout_gator.svg", 150, "Scout the alligator holding a magnifying glass")}<h1>Scout</h1></div>
  <div class="tagline">Story leads from the public record, checked before you see them</div>
</div>
""")

NEWS_VALUE_COLORS = {  # chip background, text color
    "Impact": ("#E3EAF5", "#1D3B66"), "Conflict": ("#F8E1E4", "#8A1C2B"), "Timeliness": ("#FCEFD9", "#7A4A00"),
    "Proximity": ("#DDF1EE", "#0F5A50"), "Prominence": ("#EDE4F6", "#4E2A7A"), "Unusual": ("#FDE6D8", "#8A3A0A"),
    "Currency": ("#DFF0FA", "#0D4F73"), "Human interest": ("#FBE3EF", "#82204F"), "So what": ("#E9E9E9", "#333333"),
    "Verified evidence": ("#E2F2E2", "#225C22"),
}


ABBREVIATIONS = {"jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec", "st", "dr",
                 "rd", "ave", "mr", "ms", "mrs", "no", "co", "inc", "vs", "u.s", "s.c", "a.m", "p.m", "jr", "sr"}


def first_sentence(text: str) -> tuple[str, str]:
    """Split a summary into its first sentence and the rest, without breaking at "Nov." or "St."."""
    text = (text or "").strip()
    for m in re.finditer(r"(?<=[.!?])\s+(?=[A-Z0-9“\"])", text):
        last_word = text[:m.start()].rsplit(" ", 1)[-1].rstrip(".").lower()
        if last_word not in ABBREVIATIONS:
            return text[:m.start()], text[m.end():]
    return text, ""


def money_line(card: dict) -> str:
    """Before -> after in big type, when the lead is a dollar change."""
    if card.get("dollar_change") is None or not card.get("amount_before"):
        return ""
    change = card["dollar_change"]
    try:
        before = float(card["amount_before"].replace("$", "").replace(",", ""))
        pct = f" ({change / before:+.0%})" if before else ""
    except ValueError:
        pct = ""
    sign = "+" if change >= 0 else "−"
    return (f'<div class="money"><span>{esc(card["amount_before"])}</span><span class="arrow">→</span>'
            f'<span>{esc(card["amount_after"])}</span><span class="delta">{sign}${abs(change):,.0f}{pct}</span></div>')


def section(art: str, art_label: str, title: str, subtitle: str, body: str) -> str:
    """A newspaper-style fold-out section with a Scout drawing beside its title."""
    return (f'<details class="section"><summary>{image(art, 96, art_label)}'
            f'<span class="sec-text"><span class="sec-title">{esc(title)}</span>'
            f'<span class="sec-sub">{esc(subtitle)}</span></span><span class="sec-open"></span></summary>'
            f'<div class="sec-body">{body}</div></details>')


def fold(title: str, body: str) -> str:
    return f'<details><summary>{title}</summary><div class="fold">{body}</div></details>'


def contact_html(card: dict) -> str:
    """People named in the lead (official contact info only) and offices for the beat."""
    found = contacts_for(card, state.get("result_beat", ""))

    def links(entry):
        bits = []
        if entry.get("email") or "@" in entry.get("contact", ""):
            email = entry.get("email") or re.search(r"[\w.+-]+@[\w.-]+", entry["contact"]).group(0)
            bits.append(f'<a href="mailto:{esc(email)}">{esc(email)}</a>')
        if entry.get("phone"):
            bits.append(f'<a href="tel:{re.sub(r"[^0-9]", "", entry["phone"])}">{esc(entry["phone"])}</a>')
        bits.append(f'<a href="{esc(entry["source"])}" target="_blank">official page</a>')
        return " · ".join(bits)

    rows = []
    if found["people"]:
        rows.append('<div class="who-head">Named in this lead</div>')
        rows += [f'<div class="who"><b>{esc(p["name"])}</b>, {esc(p["title"])}<div class="who-links">{links(p)}</div></div>'
                 for p in found["people"]]
    rows.append('<div class="who-head">Offices to call</div>')
    for o in found["offices"]:
        who = f' ({esc(o["contact"].split(",")[0])})' if o.get("contact") else ""
        note = f'<div class="who-note">{esc(o["note"])}</div>' if o.get("note") else ""
        rows.append(f'<div class="who"><b>{esc(o["name"])}</b>{who}<div class="who-links">{links(o)}</div>{note}</div>')
    rows.append('<div class="who-note">Contact details for public officials and offices only, from government websites '
                '(checked Oct. 25, 2026). Confirm before you call.</div>')
    return "".join(rows)


def card_html(card: dict) -> str:
    values = [v for v in card["news_values"] if v != "So what"]  # a test, never a tag
    chips = "".join(
        f'<span class="chip" style="background:{NEWS_VALUE_COLORS.get(v, ("#EEE", "#333"))[0]};'
        f'color:{NEWS_VALUE_COLORS.get(v, ("#EEE", "#333"))[1]}">{esc(v)}</span>' for v in values)
    lede, rest = first_sentence(card["lead"])

    covered = overlapping(card.get("project") or "", state.get("coverage", []))
    if covered:
        links = "; ".join(f'<a href="{esc(c["url"])}" target="_blank">{esc(c["source"])}, {c["date"]:%b %d}</a>'
                          for c in covered[:3])
        news_tag = f'<span class="tag hot">📰 In the news: {links}</span>'
    elif state.get("coverage"):
        news_tag = '<span class="tag">📰 Not in local news in the last 30 days</span>'
    else:
        news_tag = ""

    evidence = "".join(
        f'<div class="quote"><span class="file">{esc(e["file"])}</span><span class="q">“{esc(e["quote"])}”</span>'
        f'<span class="note">{esc(e["what_it_shows"])}</span></div>' for e in card["evidence"])
    if card.get("quotes_removed"):
        evidence += (f'<div class="quote"><span class="note">{card["quotes_removed"]} quote(s) left out because '
                     'they could not be found word for word in the original file.</span></div>')
    steps = "<ul>" + "".join(f"<li>{esc(s)}</li>" for s in card["next_steps"]) + "</ul>"
    more = esc(rest) + (" " if rest else "") + f'<p class="why"><b>Why it could matter:</b> {esc(card["why_it_surfaced"])}</p>'
    notice = f'<div class="notice"><b>Note</b> &nbsp;{esc(card["notice"])}</div>' if card.get("notice") else ""

    return f"""
    <div class="card">
      <div class="kicker">{esc(LEAD_TYPES.get(card["lead_type"], card["lead_type"]))}</div>
      <h3>{esc(card["title"])}</h3>
      <div class="nv"><span class="nv-label">News values</span>{chips}</div>
      {money_line(card)}
      <div class="dek">{esc(lede)}</div>
      {notice}
      <div class="tags">{news_tag}</div>
      <div class="folds">
        {fold("More detail", more)}
        {fold(f"Evidence ({len(card['evidence'])})", evidence)}
        {fold("Good to know" if card["lead_type"] in ("Event", "Opening or closing") else "Another explanation to rule out",
              esc(card["alternative_explanation"]))}
        {fold("How to report it", steps)}
        {fold("Who to contact", contact_html(card))}
      </div>
    </div>"""


# ------------------------------------------------------------------ state

state = st.session_state
state.setdefault("step", "beat")  # beat -> docs -> results
state.setdefault("beat", None)
state.setdefault("files", {})  # file name -> bytes, added by the reporter
state.setdefault("uploader_key", 0)
state.setdefault("samples", set())  # optional document sets the reporter added

fresh = fixtures = False  # the app always uses the real records; scripts/run_once.py has --fresh and --fixtures


def go(step: str):
    state.step = step
    st.rerun()


def steps_bar(current: str):
    names = [("beat", "1 · Beat"), ("docs", "2 · Documents"), ("results", "3 · Story leads")]
    order = [n for n, _ in names]
    parts = []
    for name, label in names:
        cls = "on" if name == current else ("done" if order.index(name) < order.index(current) else "")
        parts.append(f'<span class="{cls}">{label}</span>')
    st.html('<div class="steps">' + '<span class="sep">—</span>'.join(parts) + "</div>")


def loader(slot, caption: str = "Loading…"):
    slot.html(f'<div class="loader">{image("notepad.svg", 92, "A pencil writing on a notepad")}'
              f'<div class="cap">{esc(caption)}</div></div>')


@st.cache_data(show_spinner=False)
def preview(filename: str, data: bytes) -> tuple[int, str | None]:
    pages, warning = extract_text(filename, data)
    return len(pages), warning


@st.cache_data(show_spinner=False)
def sample_size(name: str) -> int:
    return len(list(config.sample_text_dir(name).rglob("*.txt")))


@st.cache_data(show_spinner=False)
def county_record_count(fixtures: bool) -> int:
    return len(DocumentStore(config.FIXTURE_DATA_DIR if fixtures else config.CURRENT_DATA_DIR).docs)


def find_stories(beat: str, files: dict, samples: set | None = None):
    """Switch to the searching screen; the search itself runs there."""
    state.pending = (beat, dict(files), sorted(samples or []))
    go("searching")


def searching_screen():
    """Draw the whole searching screen first: notepad, progress bar, and blank fillers over the
    previous step's spots, so nothing from the old step lingers greyed out during the search."""
    steps_bar("results")
    pad = st.empty()
    loader(pad)
    bar = st.progress(0.0, text="Getting started…")
    for _ in range(40):
        st.empty()
    return bar


def search(bar, beat: str, files: dict, samples: list):
    """Run the search (called at the very end of the page), then show the results step."""
    def on_progress(stage, fraction):
        if fraction in PROGRESS:
            bar.progress(fraction, text=PROGRESS[fraction])

    data_dir = config.FIXTURE_DATA_DIR if fixtures else config.CURRENT_DATA_DIR
    state.events_note = ""
    if beat == "Events, openings & closings":
        try:
            name, data, _ = fetch_events()
            files = {**files, name: data}
        except EventsUnavailable as problem:
            state.events_note = str(problem)
    if files or samples:
        data_dir, _ = build_collection(list(files.items()), base_dir=data_dir, sample_sets=samples)
    state.result = run_investigation(beat, data_dir=data_dir, fresh=fresh, on_progress=on_progress)
    state.result_beat, state.result_files = beat, len(files) + sum(sample_size(n) for n in samples)
    bar.progress(1.0, text="Checking recent news coverage…")
    try:
        state.coverage, state.coverage_note = fetch_coverage(beat), ""
    except CoverageUnavailable as problem:
        state.coverage, state.coverage_note = [], str(problem)
    go("results")


# One page area that each step fully replaces, so an old step never lingers greyed out underneath.
page = st.empty()
with page.container():
    # ------------------------------------------------------------------ searching

    if state.step == "searching":
        progress_bar = searching_screen()

    # ------------------------------------------------------------------ step 1: beat

    elif state.step == "beat":
        steps_bar("beat")
        st.html('<div class="ask">What\'s your beat?</div>'
                '<div class="sub">Pick the kind of story you\'re looking for. Scout reads Beaufort County\'s project '
                'records and Council minutes and brings back story leads, each with the exact quote it came from.</div>')
        names = list(BEATS)
        for row in range(0, len(names), 2):
            cols = st.columns(2)
            for col, name in zip(cols, names[row:row + 2]):
                icon, desc = BEATS[name]
                with col.container(border=True):
                    st.html(f'<div class="beat-art">{beat_art(name, 165)}</div>'
                            f'<div class="beat">{esc(name)}</div><div class="beat-desc">{esc(desc)}</div>')
                    if st.button("Choose", key=f"beat_{name}", width="stretch",
                                 type="primary" if name == state.beat else "secondary"):
                        state.beat = name
                        go("docs")
        st.write("")
        st.caption("Just looking around?")
        if st.button(f"▶ See an example ({EXAMPLE_BEAT.lower()})"):
            state.beat, state.files = EXAMPLE_BEAT, {}
            find_stories(EXAMPLE_BEAT, {})

    # ------------------------------------------------------------------ step 2: documents

    elif state.step == "docs":
        steps_bar("docs")
        icon, _ = BEATS[state.beat]
        looks_for, worth_adding = BEAT_GUIDE[state.beat]
        st.html(f'<div class="ask-row">{beat_art(state.beat, 110)}<div class="ask">{esc(state.beat)}</div></div>'
                f'<div class="sub">Scout will look for {esc(looks_for)}.<br>'
                f'Every lead is ranked by news value and checked against recent local coverage.</div>'
                f'<div class="label">Add more documents (optional)</div>'
                f'<div class="sub">Scout always searches the past year of Beaufort County Council and committee '
                f'minutes (October 2025 to October 2026), the county\'s current project list, and its 2025–2026 '
                f'capital plan. Drop in {esc(worth_adding)} below, or add the county\'s 2020–2022 records.</div>')

        uploaded = st.file_uploader("Drop minutes or agendas here", type=["pdf", "txt", "html", "htm"],
                                    accept_multiple_files=True, key=f"uploader_{state.uploader_key}",
                                    help="PDF files with selectable text, plain text files, or a saved web page.")
        for f in uploaded or []:
            pages, warning = preview(f.name, f.getvalue())
            if warning:
                st.warning(warning, icon="📄")
            else:
                state.files[f.name] = f.getvalue()
        if uploaded and all(f.name in state.files for f in uploaded):  # move them to the list and clear the box
            state.uploader_key += 1
            st.rerun()

        for name, info in config.SAMPLE_SETS.items():
            if state.beat not in info["beats"]:
                continue
            added = name in state.samples
            with st.container(border=True):
                st.html(f'<div class="beat">{"✅" if added else "🏛️"} {esc(info["label"])}</div>'
                        f'<div class="beat-desc">{sample_size(name)} meetings, {esc(info["dates"])}. '
                        f'{"Added: Scout will read them too." if added else "Add them and Scout will read them too."}</div>')
                if st.button("Remove" if added else "Add these", key=f"sample_{name}", width="stretch"):
                    state.samples.symmetric_difference_update({name})
                    st.rerun()

        if state.beat == "Events, openings & closings":
            with st.container(border=True):
                st.html('<div class="beat">🗓️ Today\'s event calendars</div><div class="beat-desc">When you search, '
                        'Scout checks the Beaufort County, Hilton Head Island, and Port Royal calendars for the next '
                        '45 days and flags what\'s worth covering.</div>')

        if state.beat == "Public safety":
            with st.container(border=True):
                st.html('<div class="beat">🚔 Check today\'s jail log</div><div class="beat-desc">Adds everyone '
                        'booked into the Beaufort County Detention Center in the last 72 hours. Home addresses, '
                        'birth dates, race, and physical details are left out.</div>')
                if st.button("Check the jail log", width="stretch"):
                    pad = st.empty()
                    loader(pad, "Getting the jail log…")
                    try:
                        name, data, count = fetch_jail_roster()
                        state.files[name] = data
                        st.toast(f"Added the jail log: {count} bookings.", icon="🚔")
                    except FetchFailed as problem:
                        st.error(str(problem), icon="⚠️")
                    finally:
                        pad.empty()

        if state.files:
            st.html('<div class="label">Your documents</div>')
            for name in list(state.files):
                pages = preview(name, state.files[name])[0]
                left, right = st.columns([5, 1], vertical_alignment="center")
                left.markdown(f"📄 **{name}** · {pages} page{'s' if pages != 1 else ''}")
                if right.button("Remove", key=f"remove_{name}"):
                    del state.files[name]
                    st.rerun()

        st.write("")
        back, forward = st.columns([1, 2])
        if back.button("← Change beat", width="stretch"):
            go("beat")
        if forward.button(f"Find {state.beat.lower()} stories", type="primary", width="stretch"):
            find_stories(state.beat, state.files, {s for s in state.samples
                                                   if state.beat in config.SAMPLE_SETS[s]["beats"]})

    # ------------------------------------------------------------------ step 3: story leads

    else:
        steps_bar("results")
        result = state.result
        icon = BEATS.get(state.result_beat, ("", ""))[0]
        extra = f" plus {state.result_files} added document{'s' if state.result_files != 1 else ''}" if state.result_files else ""
        source_line = ("From today's Beaufort County, Hilton Head Island, and Port Royal event calendars."
                       if state.result_beat == "Events, openings & closings"
                       else f"From {county_record_count(fixtures)} Beaufort County records{extra}.")
        st.html(f'<div class="ask-row">{beat_art(state.result_beat, 110)}<div class="ask">{esc(state.result_beat)}</div></div>'
                f'<div class="sub">{source_line}</div>')

        if result.status == "complete":
            n = len(result.leads)
            if n:
                st.success(f"Scout found {n} story lead{'s' if n != 1 else ''}. All are preliminary and not "
                           "independently verified: starting points, not findings.", icon="📰")
            else:
                st.info("No strong leads this time. Start over with another beat, or add more documents.", icon="📰")
        elif result.status == "stopped":
            st.warning(result.message, icon="⏸️")
        else:
            st.error(result.message, icon="⚠️")
        for warning in result.warnings:
            st.warning(warning.replace("Suspicious instructions found in", "A document tried to give Scout instructions:")
                       .replace("; they were ignored.", ". Scout ignored them."), icon="🛡️")

        if state.get("events_note"):
            st.warning(state.events_note, icon="🗓️")

        booked = result.jail.get("bookings_checked", 0)
        if booked and result.status == "complete":
            arrests = sum(card["lead_type"] == "Arrest record" for card in result.leads)
            ice = result.jail.get("ice_holds", 0)
            ice_note = f" The log also lists {ice} ICE hold{'s' if ice != 1 else ''}." if ice else ""
            if arrests:
                st.info(f"Jail log checked: Scout read all {booked} bookings and flagged {arrests} below."
                        + ice_note, icon="🚔")
            else:
                st.info(f"Jail log checked: Scout read all {booked} bookings and found nothing "
                        "newsworthy. No serious or violent charges, cases involving children, trafficking-level "
                        "drug amounts, ICE-hold patterns, or names that also appear in the public "
                        "records." + ice_note, icon="🚔")

        for card in result.leads:
            st.html(card_html(card))

        if state.get("coverage"):
            stories = "".join(
                f'<div class="item"><a href="{esc(c["url"])}" target="_blank">{esc(c["title"])}</a>'
                f'<div class="meta">{esc(c["source"])} · {c["date"]:%B %d, %Y}</div></div>' for c in state.coverage)
            n = len(state.coverage)
            st.html(section("scout_newspaper.svg", "Scout reading the local news",
                            "Recent local coverage on this beat",
                            f"{n} stor{'ies' if n != 1 else 'y'} from the last 30 days", stories))
        elif state.get("coverage_note"):
            st.caption(state.coverage_note)

        if result.killed:
            dropped = "".join(f'<div class="item"><b>{esc(k["title"])}</b><div class="meta why">{esc(k["reason"])}</div></div>'
                              for k in result.killed)
            n = len(result.killed)
            st.html(section("scout_x.svg", "Scout holding up a red X", "Leads Scout set aside",
                            f"{n} possible lead{'s' if n != 1 else ''}, and why each didn't make the cut", dropped))

        st.write("")
        if st.button("Start over", type="primary", width="stretch"):
            for key in ("beat", "files", "result", "coverage", "coverage_note", "samples"):
                state.pop(key, None)
            go("beat")

st.html('<div class="footer">Scout points to records worth checking. Its leads are not findings and never an '
        'accusation of wrongdoing. Confirm everything with the original documents and the people involved.</div>')

if state.step == "searching":  # last, so the whole searching screen is already drawn
    search(progress_bar, *state.pop("pending"))
