"""Cost per run, per user per month, and at scale — from real measured runs.

Uses every completed FRESH run on the REAL Beaufort County records saved in runs/
(fresh runs bypass all caches, so their token counts are what a run really costs).

Usage:
    python scripts/cost_report.py
    python scripts/cost_report.py --runs-per-month 20

Prices come from leads/config.py (PRICE_*_PER_M, US dollars per 1 million tokens).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leads import config  # noqa: E402
from leads.costs import cost_usd, prices_set  # noqa: E402

# Assumption: a county reporter runs a scan about once per working day (~20 per month).
DEFAULT_RUNS_PER_MONTH = 20


def data_source(info: dict, run_dir: Path) -> str:
    """Older runs did not record their data source; their trace says how many documents they read."""
    if "data" in info:
        return info["data"]
    start = json.loads((run_dir / "trace.json").read_text())[0]["summary"]
    return "fixtures" if " 7 documents" in start else "real"


def measured_runs(since: str = "") -> list[dict]:
    runs = []
    for result_file in sorted(config.RUNS_DIR.glob("*/result.json")):
        info = json.loads(result_file.read_text())
        if info["run_id"] < since or info.get("status") != "complete" or not info.get("fresh", True):
            continue
        if data_source(info, result_file.parent) != "real":
            continue
        total = json.loads((result_file.parent / "usage.json").read_text())[-1]
        if total["app_cache_hits"]:
            continue
        runs.append({"run_id": info["run_id"], "cache_write_tokens": total.get("cache_write_tokens", 0),
                     **{k: total[k] for k in ("calls", "input_tokens", "cached_input_tokens", "output_tokens")}})
    return runs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-per-month", type=int, default=DEFAULT_RUNS_PER_MONTH)
    parser.add_argument("--since", default="", help="only count runs whose id is at or after this, e.g. 20261024-1044")
    parser.add_argument("--portkey-cost", type=float, default=None,
                        help="dollars one search cost, read from the Portkey dashboard (Logs, filter by the run's trace id)")
    args = parser.parse_args()

    runs = measured_runs(args.since)
    if not runs:
        sys.exit("No fresh runs on the real data found in runs/. Run: python scripts/run_once.py 'Public spending' --fresh")

    lines = ["# Cost report (measured)", "", f"Model: {config.MODEL}. Fresh runs on the real Beaufort County records.", "",
             "| Run | Model calls | Input tokens | Cached input | Output tokens | Cost |", "|---|---|---|---|---|---|"]
    for r in runs:
        c = cost_usd(r["input_tokens"], r["cached_input_tokens"], r["output_tokens"], r["cache_write_tokens"])
        lines.append(f"| {r['run_id']} | {r['calls']} | {r['input_tokens']:,} | {r['cached_input_tokens']:,} | "
                     f"{r['output_tokens']:,} | {f'${c:.4f}' if c is not None else 'price not set'} |")
    n = len(runs)
    avg = {k: sum(r[k] for r in runs) / n for k in ("input_tokens", "cached_input_tokens", "output_tokens",
                                                     "cache_write_tokens")}
    lines += ["", f"**Typical run (average of {n}):** {avg['input_tokens']:,.0f} input tokens "
              f"({avg['cached_input_tokens'] / avg['input_tokens']:.0%} cached), {avg['output_tokens']:,.0f} output tokens.", ""]

    if args.portkey_cost is not None:
        per_run, per_user = args.portkey_cost, args.portkey_cost * args.runs_per_month
        lines += [f"Measured in the Portkey dashboard: one fresh search cost ${per_run:.4f}.", "",
                  "| | Cost |", "|---|---|",
                  f"| One search | ${per_run:.4f} |",
                  f"| One reporter per month ({args.runs_per_month} searches, assumed) | ${per_user:.2f} |",
                  f"| 100 reporters per month | ${per_user * 100:,.2f} |",
                  f"| 10,000 reporters per month | ${per_user * 10_000:,.2f} |", "",
                  "Assumption: every search is fresh. Repeat searches answered from the app cache cost nothing, "
                  "so real costs would be lower."]
    elif not prices_set():
        lines.append("Prices are not set in leads/config.py, so dollar figures cannot be computed yet. "
                     "Or pass --portkey-cost with the dollars one search cost in the Portkey dashboard.")
    else:
        per_run = cost_usd(avg["input_tokens"], avg["cached_input_tokens"], avg["output_tokens"], avg["cache_write_tokens"])
        per_user = per_run * args.runs_per_month
        lines += [f"gpt-6-luna prices per 1M tokens (Portkey's public price list): input ${config.PRICE_INPUT_PER_M}, "
                  f"cached input ${config.PRICE_CACHED_INPUT_PER_M}, cache write ${config.PRICE_CACHE_WRITE_PER_M}, "
                  f"output ${config.PRICE_OUTPUT_PER_M}.", "",
                  "| | Cost |", "|---|---|",
                  f"| One run | ${per_run:.4f} |",
                  f"| One user per month ({args.runs_per_month} runs, assumed) | ${per_user:.2f} |",
                  f"| 100 users per month | ${per_user * 100:,.2f} |",
                  f"| 10,000 users per month | ${per_user * 10_000:,.2f} |", "",
                  "Assumption: every run is fresh. Repeat runs served from the app cache cost nothing, "
                  "so real costs would be lower."]

    text = "\n".join(lines) + "\n"
    print(text)
    out = config.RUNS_DIR / "cost_report.md"
    out.write_text(text)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
