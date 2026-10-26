"""Talking to the model: API key, client, token logging, caching, and the budget check.

The client setup is copied from the course's HW1 (Portkey in front of OpenAI).
"""

import csv
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values
from openai import OpenAI
from openai.types.chat import ChatCompletion

from . import config
from .guards import TokenBudget


class MissingKey(Exception):
    """No PORTKEY_API_KEY was found."""


def load_api_key(project_dir: Path = config.PROJECT_DIR) -> str:
    """Look for the key in .env in the project folder, then one folder above."""
    for folder in (project_dir, project_dir.parent):
        key = (dotenv_values(folder / ".env").get(config.API_KEY_NAME) or "").strip()
        if key:
            return key
    key = os.getenv(config.API_KEY_NAME, "").strip()
    if key:
        return key
    raise MissingKey(
        f"No {config.API_KEY_NAME} found. Put a .env file containing {config.API_KEY_NAME}=your-key "
        "in the app folder or the folder above it, then restart the app."
    )


def make_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url=config.PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": api_key, "x-portkey-provider": "openai"},
    )


class UsageLog:
    """Token counts for every model call in a run, saved to runs/token_log.csv."""

    FIELDS = ["run_id", "time", "agent", "call", "input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens", "from_app_cache"]

    def __init__(self, run_id: str, log_file: Path = config.RUNS_DIR / "token_log.csv"):
        self.run_id = run_id
        self.log_file = log_file
        self.rows: list[dict] = []

    def add(self, agent: str, input_tokens: int, cached_input_tokens: int, output_tokens: int,
            from_app_cache: bool, cache_write_tokens: int = 0):
        row = {
            "run_id": self.run_id, "time": datetime.now().isoformat(timespec="seconds"), "agent": agent,
            "call": sum(1 for r in self.rows if r["agent"] == agent) + 1,
            "input_tokens": input_tokens, "cached_input_tokens": cached_input_tokens,
            "cache_write_tokens": cache_write_tokens, "output_tokens": output_tokens, "from_app_cache": from_app_cache,
        }
        self.rows.append(row)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        new_file = not self.log_file.exists()
        with self.log_file.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS)
            if new_file:
                writer.writeheader()
            writer.writerow(row)

    def summary(self) -> list[dict]:
        """One row per agent plus a total row."""
        table = {}
        for r in self.rows:
            s = table.setdefault(r["agent"], {"agent": r["agent"], "calls": 0, "input_tokens": 0,
                                              "cached_input_tokens": 0, "cache_write_tokens": 0,
                                              "output_tokens": 0, "app_cache_hits": 0})
            s["calls"] += 1
            s["app_cache_hits"] += int(r["from_app_cache"])
            for key in ("input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens"):
                s[key] += r[key]
        rows = list(table.values())
        total = {"agent": "TOTAL"}
        for key in ("calls", "input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens", "app_cache_hits"):
            total[key] = sum(r[key] for r in rows)
        return rows + [total]


class LLM:
    """One model connection for one run: logs every call and enforces the token budget."""

    def __init__(self, client, usage: UsageLog, budget: TokenBudget,
                 use_cache: bool = True, cache_dir: Path = config.RUNS_DIR / "cache"):
        # Every call in a run carries the run id as its Portkey trace id, so the Portkey dashboard
        # can show exactly what one search cost (Logs, filtered by trace id).
        self.client = client
        self.usage = usage
        self.budget = budget
        self.use_cache = use_cache
        self.cache_dir = cache_dir

    def call(self, agent: str, messages: list[dict], tools: list[dict] | None = None,
             tool_choice: str | dict | None = None) -> ChatCompletion:
        request = {"model": config.MODEL, "messages": messages}
        if tools:
            request["tools"] = tools
            request["reasoning_effort"] = config.REASONING_EFFORT
        if tool_choice:
            request["tool_choice"] = tool_choice

        cache_file = self.cache_dir / (hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest() + ".json")
        if self.use_cache and cache_file.exists():  # app-level cache: identical request, no tokens spent
            self.usage.add(agent, 0, 0, 0, from_app_cache=True)
            return ChatCompletion.model_validate_json(cache_file.read_text())

        self.budget.check()  # raises BudgetExceeded before spending more
        response = self.client.chat.completions.create(
            **request, extra_headers={"x-portkey-trace-id": self.usage.run_id})

        usage = response.usage
        details = getattr(usage, "prompt_tokens_details", None)
        cached = getattr(details, "cached_tokens", 0) or 0  # provider-side cache reads, as reported by the API
        written = getattr(details, "cache_write_tokens", 0) or 0  # tokens newly stored in the provider cache
        self.usage.add(agent, usage.prompt_tokens, cached, usage.completion_tokens,
                       from_app_cache=False, cache_write_tokens=written)
        self.budget.add(usage.prompt_tokens, usage.completion_tokens)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(response.model_dump_json())
        return response
