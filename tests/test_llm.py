"""Token logging, app caching, the budget stop, and key loading — with a fake model (no API calls)."""

import pytest
from openai.types.chat import ChatCompletion

from leads import llm
from leads.guards import BudgetExceeded, TokenBudget


def fake_response(text="ok", input_tokens=1_000, cached=0, output_tokens=200) -> ChatCompletion:
    return ChatCompletion.model_validate({
        "id": "fake", "object": "chat.completion", "created": 0, "model": "gpt-6-luna",
        "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": text}}],
        "usage": {"prompt_tokens": input_tokens, "completion_tokens": output_tokens,
                  "total_tokens": input_tokens + output_tokens, "prompt_tokens_details": {"cached_tokens": cached}},
    })


class FakeClient:
    """Stands in for the OpenAI client and counts how often the 'model' is called."""

    def __init__(self, **usage):
        self.calls = 0
        self.usage = usage
        self.chat = self
        self.completions = self

    def create(self, **request):
        self.calls += 1
        return fake_response(**self.usage)


def make_llm(tmp_path, client, budget=100_000, use_cache=True):
    usage = llm.UsageLog("test-run", log_file=tmp_path / "token_log.csv")
    return llm.LLM(client, usage, TokenBudget(budget), use_cache=use_cache, cache_dir=tmp_path / "cache")


MESSAGES = [{"role": "user", "content": "hello"}]


def test_tokens_are_logged_per_agent_including_cached_tokens(tmp_path):
    model = make_llm(tmp_path, FakeClient(input_tokens=1_000, cached=600, output_tokens=200), use_cache=False)
    model.call("Scout", MESSAGES)
    model.call("Skeptic", MESSAGES)
    summary = {row["agent"]: row for row in model.usage.summary()}
    assert summary["Scout"]["cached_input_tokens"] == 600
    assert summary["TOTAL"]["input_tokens"] == 2_000
    assert (tmp_path / "token_log.csv").read_text().count("\n") == 3  # header + 2 calls


def test_repeat_request_is_served_from_app_cache_without_spending_tokens(tmp_path):
    client = FakeClient()
    model = make_llm(tmp_path, client)
    first = model.call("Scout", MESSAGES)
    second = model.call("Scout", MESSAGES)
    assert client.calls == 1  # the model was only asked once
    assert second.choices[0].message.content == first.choices[0].message.content
    assert model.usage.summary()[-1]["app_cache_hits"] == 1


def test_fresh_run_bypasses_the_cache(tmp_path):
    client = FakeClient()
    make_llm(tmp_path, client).call("Scout", MESSAGES)
    make_llm(tmp_path, client, use_cache=False).call("Scout", MESSAGES)
    assert client.calls == 2


def test_run_stops_cleanly_when_token_budget_is_spent(tmp_path):
    client = FakeClient(input_tokens=1_000, output_tokens=200)
    model = make_llm(tmp_path, client, budget=2_000, use_cache=False)
    model.call("Scout", MESSAGES)  # 1,200 tokens used
    model.call("Connector", MESSAGES)  # 2,400 tokens used: over budget
    with pytest.raises(BudgetExceeded, match="stopped early"):
        model.call("Skeptic", MESSAGES)
    assert client.calls == 2  # the third call never reached the model


def test_key_is_found_in_the_folder_above(tmp_path, monkeypatch):
    monkeypatch.delenv("PORTKEY_API_KEY", raising=False)
    project = tmp_path / "repo"
    project.mkdir()
    (tmp_path / ".env").write_text("PORTKEY_API_KEY=key-from-parent\n")
    assert llm.load_api_key(project) == "key-from-parent"


def test_project_env_wins_over_folder_above(tmp_path, monkeypatch):
    monkeypatch.delenv("PORTKEY_API_KEY", raising=False)
    project = tmp_path / "repo"
    project.mkdir()
    (tmp_path / ".env").write_text("PORTKEY_API_KEY=key-from-parent\n")
    (project / ".env").write_text("PORTKEY_API_KEY=key-from-project\n")
    assert llm.load_api_key(project) == "key-from-project"


def test_missing_key_gives_a_plain_message(tmp_path, monkeypatch):
    monkeypatch.delenv("PORTKEY_API_KEY", raising=False)
    project = tmp_path / "repo"
    project.mkdir()
    with pytest.raises(llm.MissingKey, match="Put a .env file"):
        llm.load_api_key(project)


def test_a_stalled_ai_call_times_out_instead_of_hanging():
    client = llm.make_client("test-key")
    assert client.timeout == llm.config.MODEL_TIMEOUT_SECONDS and client.max_retries == llm.config.MODEL_RETRIES
