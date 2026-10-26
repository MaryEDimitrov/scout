"""Safety features 3 and 4: runaway agents and overspending are stopped by hard limits."""

import pytest

from leads.guards import BudgetExceeded, TokenBudget, ToolCallCounter, ToolLimitReached


def test_agent_stops_at_its_tool_call_limit():
    counter = ToolCallCounter(per_agent=3, per_run=100)
    for _ in range(3):
        counter.record("Scout")
    with pytest.raises(ToolLimitReached, match="Scout reached its limit of 3"):
        counter.record("Scout")


def test_run_stops_at_its_tool_call_limit_across_agents():
    counter = ToolCallCounter(per_agent=10, per_run=5)
    for agent in ["Scout", "Scout", "Connector", "Connector", "Skeptic"]:
        counter.record(agent)
    with pytest.raises(ToolLimitReached, match="run reached its limit of 5"):
        counter.record("Skeptic")


def test_token_budget_stops_the_run_with_a_plain_message():
    budget = TokenBudget(max_tokens=1_000)
    budget.check()  # fine at the start
    budget.add(input_tokens=800, output_tokens=250)
    with pytest.raises(BudgetExceeded, match="budget of 1,000"):
        budget.check()
