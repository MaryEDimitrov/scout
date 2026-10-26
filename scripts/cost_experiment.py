"""Cost-cutting experiment: does sending the model less text cut tokens without hurting quality?

  baseline : the normal tool output sizes in leads/config.py
  lean     : shorter pages, snippets, and result lists from every tool

Both run on the SYNTHETIC test collection, so quality is scored against the answer key.

Usage:
    python scripts/cost_experiment.py --runs 3
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluate import evaluate, save  # noqa: E402

from leads import config  # noqa: E402
from leads.costs import cost_usd  # noqa: E402

LEAN = {"MAX_SECTION_CHARS": 2_500, "MAX_SEARCH_RESULTS": 4, "SNIPPET_CHARS": 180, "LOOKUP_SNIPPET_CHARS": 200}


def averages(rows):
    done = [r for r in rows if r["score"]]
    n = len(done) or 1
    avg = {k: sum(r["tokens"][k] for r in done) / n for k in ("input_tokens", "cached_input_tokens", "output_tokens")}
    avg["planted"] = sum(r["score"]["planted_found"] for r in done) / n
    avg["decoys"] = sum(r["score"]["decoys_avoided"] for r in done) / n
    avg["injection"] = sum(r["score"]["injection"]["defended"] for r in done)
    avg["runs"] = len(done)
    avg["cost"] = cost_usd(avg["input_tokens"], avg["cached_input_tokens"], avg["output_tokens"])
    return avg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()

    baseline = evaluate(args.runs, label="baseline")
    original = {k: getattr(config, k) for k in LEAN}
    for k, v in LEAN.items():
        setattr(config, k, v)
    try:
        lean = evaluate(args.runs, label="lean")
    finally:
        for k, v in original.items():
            setattr(config, k, v)

    summary = {"baseline": averages(baseline), "lean": averages(lean), "lean_settings": LEAN,
               "baseline_settings": original}
    b, l = summary["baseline"], summary["lean"]
    change = (l["input_tokens"] - b["input_tokens"]) / b["input_tokens"] * 100 if b["input_tokens"] else 0
    table = ["| Setting | Runs | Avg input tokens | Avg cached | Avg output | Avg cost | Planted found (of 3) | Decoys avoided (of 3) | Injection defended |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name, a in (("baseline", b), ("lean", l)):
        cost = f"${a['cost']:.4f}" if a["cost"] is not None else "price not set"
        table.append(f"| {name} | {a['runs']} | {a['input_tokens']:,.0f} | {a['cached_input_tokens']:,.0f} | "
                     f"{a['output_tokens']:,.0f} | {cost} | {a['planted']:.1f} | {a['decoys']:.1f} | {a['injection']}/{a['runs']} |")
    text = "\n".join(table) + f"\n\nLean context changed average input tokens by {change:+.0f}%.\n"
    print("\n" + text)
    path = save(baseline + lean, "cost-experiment")
    path.write_text(path.read_text() + "\n## Summary\n\n" + text)
    (path.with_suffix(".summary.json")).write_text(json.dumps(summary, indent=2))
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
