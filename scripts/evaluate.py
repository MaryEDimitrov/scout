"""Run the app on the SYNTHETIC test collection and report what it got right.

Usage:
    python scripts/evaluate.py            # 3 fresh runs (real API calls)
    python scripts/evaluate.py --runs 1

Reports, for each run: which planted leads were found, which decoys were dismissed,
whether the prompt injection was defended, and tokens used. Saves a copy to runs/evaluation/.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leads import config  # noqa: E402
from leads.evaluation import score  # noqa: E402
from leads.pipeline import run_investigation  # noqa: E402


def evaluate(runs: int, area: str = "Public spending", label: str = "baseline") -> list[dict]:
    rows = []
    for i in range(1, runs + 1):
        print(f"Run {i}/{runs} ({label})…", flush=True)
        result = run_investigation(area, data_dir=config.FIXTURE_DATA_DIR, fresh=True)
        total = result.usage_summary[-1] if result.usage_summary else {}
        rows.append({"run": i, "label": label, "run_id": result.run_id, "status": result.status,
                     "score": score(result) if result.status == "complete" else None,
                     "tokens": {k: total.get(k, 0) for k in ("input_tokens", "cached_input_tokens", "output_tokens")}})
    return rows


def report(rows: list[dict]) -> str:
    lines = ["| Run | Status | Planted found | Decoys avoided | Injection defended | Input tokens | Cached | Output |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        s, t = r["score"], r["tokens"]
        if s:
            lines.append(f"| {r['label']} {r['run']} | {r['status']} | {s['planted_found']}/{s['planted_total']} | "
                         f"{s['decoys_avoided']}/{s['decoys_total']} | {'yes' if s['injection']['defended'] else 'NO'} | "
                         f"{t['input_tokens']:,} | {t['cached_input_tokens']:,} | {t['output_tokens']:,} |")
        else:
            lines.append(f"| {r['label']} {r['run']} | {r['status']} | – | – | – | {t['input_tokens']:,} | "
                         f"{t['cached_input_tokens']:,} | {t['output_tokens']:,} |")
    lines.append("")
    for r in rows:
        if r["score"]:
            s = r["score"]
            lines.append(f"**{r['label']} run {r['run']}** ({r['run_id']})")
            lines += [f"- {p['id']} {'FOUND' if p['found'] else 'missed'}: {p['story']}" for p in s["planted"]]
            lines += [f"- {d['id']} {d['outcome']}: {d['story']}" for d in s["decoys"]]
            inj = s["injection"]
            lines.append(f"- Injection: attack phrases in output: {inj['attack_phrases_in_output'] or 'none'}; "
                         f"confidence fixed by code: {inj['confidence_fixed_by_code']}; targeted lead survived: "
                         f"{inj['targeted_lead_survived']}; warning shown: {inj['warning_shown']}")
            lines.append("")
    return "\n".join(lines)


def save(rows: list[dict], name: str) -> Path:
    out = config.RUNS_DIR / "evaluation"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (out / f"{stamp}-{name}.json").write_text(json.dumps(rows, indent=2))
    path = out / f"{stamp}-{name}.md"
    path.write_text(f"# Evaluation on the synthetic test collection ({name})\n\n" + report(rows) + "\n")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    rows = evaluate(args.runs)
    print("\n" + report(rows))
    print(f"Saved: {save(rows, 'baseline')}")
