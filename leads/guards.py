"""Hard limits that stop runaway agents and overspending."""

from collections import Counter

from . import config


class ToolLimitReached(Exception):
    """An agent or the whole run used up its tool calls."""


class BudgetExceeded(Exception):
    """The run used up its token budget."""


class ToolCallCounter:
    def __init__(self, per_agent: int = config.MAX_TOOL_CALLS_PER_AGENT, per_run: int = config.MAX_TOOL_CALLS_PER_RUN):
        self.per_agent = per_agent
        self.per_run = per_run
        self.counts: Counter[str] = Counter()

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def record(self, agent: str) -> None:
        """Call before every tool call. Raises once a limit is hit."""
        if self.counts[agent] >= self.per_agent:
            raise ToolLimitReached(f"{agent} reached its limit of {self.per_agent} tool calls.")
        if self.total >= self.per_run:
            raise ToolLimitReached(f"The run reached its limit of {self.per_run} tool calls.")
        self.counts[agent] += 1


class TokenBudget:
    def __init__(self, max_tokens: int = config.TOKEN_BUDGET_PER_RUN):
        self.max_tokens = max_tokens
        self.used = 0

    @property
    def remaining(self) -> int:
        return max(self.max_tokens - self.used, 0)

    def check(self) -> None:
        """Call before every model call. Raises once the budget is spent."""
        if self.used >= self.max_tokens:
            raise BudgetExceeded(
                f"This run used {self.used:,} tokens, reaching its budget of {self.max_tokens:,}. "
                "It stopped early to avoid overspending; results so far are shown."
            )

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.used += input_tokens + output_tokens
