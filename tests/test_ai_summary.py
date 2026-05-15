"""
Tests for the AI summary fallback.

The important guarantee: with no API key the summary still works, always
returns the same four parts plus a source, and the decision-relevant fields
(next action, escalation) come from the rule-based engine -- not an LLM.
"""

import pytest

from src.ai_summary import generate_summary, is_llm_enabled

EXPECTED_KEYS = {
    "short_summary",
    "likely_issue",
    "next_action",
    "escalation_recommendation",
    "source",
}


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    """Force local fallback mode for every test in this file."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_fallback_returns_all_expected_fields(low_risk_ticket):
    summary = generate_summary(low_risk_ticket)
    assert set(summary.keys()) == EXPECTED_KEYS
    assert all(summary[k] for k in EXPECTED_KEYS)


def test_fallback_source_is_local(low_risk_ticket):
    assert generate_summary(low_risk_ticket)["source"] == "local-rule-based"


def test_is_llm_enabled_false_without_key():
    assert is_llm_enabled() is False


def test_sensitive_ticket_recommends_escalation(high_risk_ticket):
    summary = generate_summary(high_risk_ticket)
    assert summary["escalation_recommendation"].startswith("ESCALATE")


def test_non_sensitive_resolved_ticket_does_not_escalate(low_risk_ticket):
    summary = generate_summary(low_risk_ticket)
    assert not summary["escalation_recommendation"].startswith("ESCALATE")


def test_next_action_is_category_specific(high_risk_ticket):
    """Child Safety should get its specific action, not the generic one."""
    summary = generate_summary(high_risk_ticket)
    assert "Child Safety" in summary["next_action"]
