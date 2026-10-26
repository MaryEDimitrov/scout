# Scout 🐊

**An AI investigative assistant for local government reporters.** Instead of asking the reporter what
to search for, three AI agents scan a folder of real Beaufort County, South Carolina public records
(the past year of County Council and committee minutes, the county's live project dashboard, and its
capital plan) and surface evidence-backed story leads:

- **Changes**: a project's cost, funding, status, or description differs between documents
- **Missing links**: a cost or project appears, but no approval or funding record exists in the collection
- **Arrest records** (only when a reporter uploads a jail log or booking report): newsworthy bookings,
  with charges quoted exactly as logged and a fixed notice that an arrest is not a conviction

Every lead shows its evidence (file name and exact quote, checked word for word in code), an
alternative innocent explanation, next steps, and a fixed confidence label: *Preliminary, not
independently verified*. The reporter decides what to pursue. It is not a chatbot and never writes
meeting summaries.

MGT 409 AI Foundations final project · Yale SOM · Mary Dimitrov

---

## Run it (about 3 minutes)

**You need:** Python 3.11 or newer, and a `.env` file containing `PORTKEY_API_KEY`.

**1. Put the key where the app looks for it.** The app looks for `.env` in this folder first, then in
the folder above it. Graders: your shared `.env` one level above the repo works as is.

```
submissions/
├── .env                 ← PORTKEY_API_KEY=... (found automatically)
└── lead-finder/         ← this repo
    ├── README.md
    └── .env.example     ← lists the only key needed
```

**2. Run one command** from inside this folder:

| Mac / Linux | Windows |
|---|---|
| `bash setup_and_run.sh` | `setup_and_run.bat` |

It creates a virtual environment in `.venv`, installs the pinned packages from `requirements.txt`,
and opens the app at **http://localhost:8501**.

<details><summary>Or do it by hand</summary>

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip install -r requirements.txt
.venv/bin/streamlit run app.py                   # Windows: .venv\Scripts\streamlit run app.py
```
</details>

**3. In the browser,** press **▶ See an example** (or choose a beat → optionally add documents →
**Find stories**). A first run takes 1–2 minutes while a notepad animation and progress bar show.
Then read the lead cards; **Possible leads Scout set aside, and why** lists what the Skeptic or the
code checks dismissed.

**For grading:** the app shows reporters only the leads. The step-by-step **run trace** for every
search is saved to `runs/<run>/trace.md`, and token counts and costs come from the scripts below
(`scripts/run_once.py` prints them after each search; `scripts/cost_report.py` totals them).

**Optional:** drag your own meeting minutes or agendas (PDF with selectable text, or .txt) into
**Add your own meeting minutes**. They are scanned together with the county collection for that run,
treated as untrusted like every other document, and stored only in `runs/uploads/` (never in `data/`).
To try it, drag in any PDF from `data/pdfs/council/`.

**Optional document sets (one click, no internet needed):** on some beats, step 2 offers more real records:
**Beaufort County project lists and Council minutes, 2020–2022 archive** (7 capital project tracker snapshots,
17 minutes and agendas, 3 backup-packet excerpts; every beat except Events). The county stopped publishing
dated project lists after 2022 (it now has a live dashboard with no saved versions), so this archive is the
only set that can show a project's cost changing across lists, as in the $900,000 overage. Also shipped in
`data/samples/`: **Hilton Head Island Town Council minutes** (21 meetings, Nov 2025–Sep 2026;
Local government, Growth & development, Housing) and **Beaufort County School District board agendas**
(19 meetings, Oct 2025–Oct 2026; Education). Sources: `data/SOURCES.md`.

**Events, openings & closings beat (needs internet):** when a reporter searches this beat, Scout reads the
next 45 days of the Beaufort County, Town of Hilton Head Island, and Town of Port Royal calendars (code drops
routine meetings) and flags fun or newsworthy events, grand openings, and closings, each quoting the
calendar line with its date, place, and link. If a calendar is down, the page says so.

**Who to contact:** each lead card lists the public officials named in it (matched from the minutes,
e.g. "Committee Chairman Lawson") with official email and phone, plus the offices to call for that beat.
Contact details come only from `data/contacts.json`, copied from government websites with source links.
Never private individuals, and never anyone named in a jail log.

**Recent coverage (needs internet):** after each search, Scout loads headlines from the last 30 days
for that beat from Google News' public feed, keeps only South Carolina outlets (there is also a Beaufort
County in North Carolina), and marks any lead whose project already appears in a recent headline. This
is plain code: headlines are never sent to the AI. If the feed can't be reached, the page says so and
everything else works.

**Optional, needs internet:** **🚔 Check the jail log** fetches the Beaufort County Detention Center's
72-hour booking roster at that moment and runs a Public safety scan on it together with the county
records. Home addresses, birth dates, race, and physical details are removed in code before the AI
sees the roster, and the fetched copy is kept only in `runs/uploads/` (never committed). These are the
app's only live connections besides the model; everything else, including **Run the example**, uses
the shipped files.

To stop the app, press `Ctrl+C` in the terminal.

---

## How it works

```
Reporter picks a beat ──► SCOUT ──candidates──► CONNECTOR ──leads + evidence──► SKEPTIC ──verdicts──► CODE CHECKS ──► lead cards
                          list_documents         lookup_project                  fetch_passage          verbatim quotes
                          search_documents       compare_passages                                       $30K threshold
                          read_section                                                                  no accusations
                                                                                                        fixed confidence
                                                                         killed leads ──► "Dismissed" log, with the reason
```

| Agent | Job | Tools (plain Python over the shipped files) |
|---|---|---|
| **Scout** | Proposes candidate leads for the chosen beat | `list_documents`, `search_documents`, `read_section` |
| **Connector** | Links each candidate across documents and does the dollar arithmetic | `lookup_project`, `compare_passages` |
| **Skeptic** | Tries to disprove each lead (contingency, change orders, phases, versions, accounting categories, records gaps) | `fetch_passage` |

Model: `gpt-6-luna` through Portkey (set once, in `leads/config.py`).

## Safety features (each has a test)

| Risk | Defense | Proof |
|---|---|---|
| Prompt injection in a document | All document text is wrapped and labeled untrusted; confidence is set by code, never by the model | `tests/test_untrusted_text.py`; live: `scripts/evaluate.py` on a planted injection document |
| Invented facts | Every evidence quote is checked word for word against its source file in code; unverifiable quotes are dropped, and a lead whose dollar figures lose their support is killed | `tests/test_verify.py`, `tests/test_pipeline.py` |
| Runaway agents | Hard caps: 20 tool calls per agent, 50 per run | `tests/test_guards.py` |
| Overspending | Token budget per run (250,000); the run stops cleanly with a plain message | `tests/test_guards.py`, `tests/test_llm.py`, `tests/test_pipeline.py` |
| Accusations | Code blocks cards with accusatory words; every card carries an alternative explanation | `tests/test_pipeline.py` |
| Arrest records | Allowed only from a reporter-uploaded log; charges quoted word for word; wording that presumes guilt is blocked; a fixed "accusation, not a conviction" notice | `tests/test_arrest_records.py` |

## Tests and scripts

```bash
.venv/bin/python -m pytest -v                                   # all tests, no API calls, ~1 second
.venv/bin/python scripts/run_once.py "Public spending"          # one run in the terminal (--fresh skips caches, --archive uses 2020-2022)
.venv/bin/python scripts/evaluate.py --runs 3                   # score against the synthetic answer key
.venv/bin/python scripts/cost_experiment.py --runs 3            # baseline vs. lean context: tokens and quality
.venv/bin/python scripts/cost_report.py                         # cost per run, per user, at 100 and 10,000 users
```

## Real data vs. test data

| Folder | What it is |
|---|---|
| `data/` | **Real, unaltered** Beaufort County public records. **Built-in collection** (always searched), in `data/current/`: 60 County Council and committee minutes, Oct 2025–Oct 2026 (PDFs in `pdfs/`, text in `text/`); a dated snapshot of the county's live Capital Projects Dashboard (`text/dashboard/`, raw county data in `raw/`); and pages 7–29 of the FY 2025–2026 Capital Improvement Plan (`text/cip_plans/`; the 116 MB original is linked in `data/SOURCES.md`). **2020–2022 archive** (one-click optional set): 7 capital project tracker snapshots (Dec 2020–Apr 2022), 17 Council/committee minutes and agendas, 3 backup-packet excerpts; PDFs in `data/pdfs/`, text in `data/text/`. Other optional sets in `data/samples/`. Sources and download dates: `data/SOURCES.md`. Leads found by hand before the app existed: `data/REFERENCE_LEADS.md`. |
| `test_fixtures/` | **Synthetic** documents for a made-up county, with 3 planted leads, 3 decoys, and 1 prompt-injection file. Answer key: `test_fixtures/answer_key.json`. |

The app reads only the shipped files. It never goes online except to call the model.

## Folder layout

```
app.py                  the web app (Streamlit)
leads/                  config, tools, agents, pipeline, quote verification, safety limits, prompts/
data/                   real records (see above)
test_fixtures/          synthetic test documents (see above)
tests/                  automated tests (no API calls)
scripts/                command-line runs, evaluation, cost report, cost experiment, PDF extraction
runs/                   token log, run traces, evaluation and cost results
docs/                   report.html, slides.html, user-study materials
```

## Limits

- "Missing" means "not found in this collection". In the 2020–2022 archive, Council records from
  April–November 2020 are not online, so approvals from that period cannot be checked.
- The county's live project dashboard keeps no history, so the built-in collection has one dated snapshot
  (`scripts/snapshot_dashboard.py` saves more). A capital plan is an estimate: a gap between the plan and a
  later budget may be a scope change.
- Results vary somewhat from run to run; the set-aside list and the run trace (`runs/<run>/trace.md`) show the reasoning each time.
- Leads are starting points for reporting, never findings.
