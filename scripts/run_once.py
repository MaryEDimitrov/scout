"""Run one investigation from the command line and print the results.

Usage:
    python scripts/run_once.py "Public spending"            # uses the app cache when possible
    python scripts/run_once.py "Public spending" --fresh    # bypasses all caches (for measuring)
    python scripts/run_once.py "Public spending" --fixtures # runs on the synthetic test documents
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leads import config  # noqa: E402
from leads.pipeline import AREAS, run_investigation  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("area", choices=list(AREAS))
    parser.add_argument("--fresh", action="store_true", help="bypass caches so tokens are really spent")
    parser.add_argument("--fixtures", action="store_true", help="use test_fixtures/ instead of the real data")
    args = parser.parse_args()

    data_dir = config.FIXTURE_DATA_DIR if args.fixtures else config.REAL_DATA_DIR
    result = run_investigation(args.area, data_dir=data_dir, fresh=args.fresh,
                               on_progress=lambda stage, fraction: print(f"  … {stage}"))

    print(f"\n{result.status.upper()}: {result.message}\n")
    for i, card in enumerate(result.leads, 1):
        print(f"LEAD {i} [{card['lead_type']}] {card['title']}")
        print(f"   {card['lead']}")
        for e in card["evidence"]:
            print(f"   - {e['file']}: \"{e['quote'][:110]}\"")
        print(f"   Alternative: {card['alternative_explanation']}\n")
    for k in result.killed:
        print(f"KILLED by {k['killed_by']}: {k['title']} — {k['reason']}")
    print("\nTokens:")
    for row in result.usage_summary:
        print(f"   {row['agent']:<10} calls={row['calls']:<3} input={row['input_tokens']:>7,} "
              f"cached={row['cached_input_tokens']:>7,} output={row['output_tokens']:>6,} "
              f"app-cache hits={row['app_cache_hits']}")
    print(f"\nTrace: {result.run_dir / 'trace.md'}")


if __name__ == "__main__":
    main()
