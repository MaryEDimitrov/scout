"""Every setting for the app lives in this one file."""

from pathlib import Path

# --- Model (the only model this project may use) ---
MODEL = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
API_KEY_NAME = "PORTKEY_API_KEY"
# gpt-6-luna only allows tool calling on /chat/completions (the HW1 endpoint) with reasoning turned off.
REASONING_EFFORT = "none"
MODEL_TIMEOUT_SECONDS = 90  # one AI call normally takes seconds; a stalled call fails instead of hanging forever
MODEL_RETRIES = 1  # one automatic retry after a timeout or dropped connection

# --- Folders ---
PROJECT_DIR = Path(__file__).resolve().parent.parent
CURRENT_DATA_DIR = PROJECT_DIR / "data" / "current" / "text"  # real county records, Oct 2025 – Oct 2026 (default)
ARCHIVE_DATA_DIR = PROJECT_DIR / "data" / "text"  # real county records, Dec 2020 – Apr 2022, with project lists
FIXTURE_DATA_DIR = PROJECT_DIR / "test_fixtures" / "text"  # synthetic test documents
RUNS_DIR = PROJECT_DIR / "runs"  # token logs and run traces

# --- Live jail log (only fetched when the reporter presses "Check the jail log") ---
JAIL_ROSTER_URL = "https://apps.beaufortcountysc.gov/inmate-inquiry/?source=booked-72h"

# --- Optional document sets a reporter can add with one click (real records, shipped in data/samples/) ---
SAMPLES_DIR = PROJECT_DIR / "data" / "samples"
SAMPLE_SETS = {
    "county_archive": {"label": "Beaufort County project lists and Council minutes (archive)",
                       "dates": "Dec 2020 – Apr 2022", "text_dir": ARCHIVE_DATA_DIR,
                       "beats": ["Public spending", "Growth & development", "Local government", "Education",
                                 "Environment & climate", "Transportation", "Housing", "Public safety"]},
    "hilton_head": {"label": "Hilton Head Island Town Council minutes", "dates": "Nov 2025 – Sep 2026",
                    "beats": ["Local government", "Growth & development", "Housing"]},
    "school_board": {"label": "Beaufort County School District board agendas", "dates": "Oct 2025 – Oct 2026",
                     "beats": ["Education"]},
}


def sample_text_dir(name: str) -> Path:
    """Where an optional set's text files live (the archive keeps its original data/text folder)."""
    return SAMPLE_SETS[name].get("text_dir", SAMPLES_DIR / name / "text")

# --- Safety limits ---
MAX_TOOL_CALLS_PER_AGENT = 20  # stops any one agent from looping forever
MAX_TOOL_CALLS_PER_RUN = 50  # stops the whole run from looping forever
TOKEN_BUDGET_PER_RUN = 250_000  # input + output tokens; the run stops cleanly past this

# --- Lead rules ---
MIN_DOLLAR_CHANGE = 30_000  # smaller changes are not flagged unless a news value justifies it
MIN_QUOTE_CHARS = 20  # shorter evidence quotes are too easy to match by accident
CONFIDENCE_LABEL = "Preliminary, not independently verified"  # set by code, never by the model
ARREST_NOTICE = ("An arrest is an accusation, not a conviction. Confirm the person's identity and the charges "
                 "with official records before publishing.")  # shown on every arrest-record card

# --- Tool output sizes (keep prompts small and cheap) ---
MAX_SECTION_CHARS = 6_000
MAX_SEARCH_RESULTS = 8
SNIPPET_CHARS = 300
LOOKUP_SNIPPET_CHARS = 360

# --- Prices for the cost summary, in US dollars per 1 million tokens ---
# gpt-6-luna list prices from Portkey's public price list (checked 2026-10-25):
# https://api.portkey.ai/model-configs/pricing/azure-openai/gpt-6-luna  (Portkey lists cents per token)
PRICE_INPUT_PER_M = 0.10
PRICE_CACHED_INPUT_PER_M = 0.01
PRICE_CACHE_WRITE_PER_M = 0.125
PRICE_OUTPUT_PER_M = 0.50
