"""A readable record of one run: which agent did what, and what it passed along."""

import json
from datetime import datetime
from pathlib import Path


class Trace:
    def __init__(self, run_id: str, run_dir: Path):
        self.run_id = run_id
        self.run_dir = run_dir
        self.events: list[dict] = []

    def add(self, actor: str, kind: str, summary: str, detail=None) -> None:
        """kind is one of: start, tool_call, handoff, code_check, verdict, stop, finish."""
        self.events.append({
            "step": len(self.events) + 1, "time": datetime.now().strftime("%H:%M:%S"),
            "actor": actor, "kind": kind, "summary": summary, "detail": detail,
        })

    def save(self) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "trace.json").write_text(json.dumps(self.events, indent=2, default=str))
        lines = [f"# Run trace: {self.run_id}", ""]
        for e in self.events:
            marker = {"handoff": "➜", "verdict": "⚖", "code_check": "✔", "stop": "■"}.get(e["kind"], "•")
            lines.append(f"{e['step']:>3}. {e['time']}  {marker} **{e['actor']}** ({e['kind']}): {e['summary']}")
        path = self.run_dir / "trace.md"
        path.write_text("\n".join(lines) + "\n")
        return path
