"""
Tests for the risk scoring logic.

These check the *behaviour we'd defend in an interview*: the score stays in
range, sensitive cases outrank trivial ones, every score comes with a reason
(explainability), and the escalation rule does what it claims.
"""

from src.risk_scoring import (
    SCORING_RULES,
    needs_escalation_flag,
    score_ticket,
)


def test_score_is_within_0_to_100(low_risk_ticket, high_risk_ticket):
    for ticket in (low_risk_ticket, high_risk_ticket):
        result = score_ticket(ticket)
        assert 0 <= result["score"] <= 100


def test_high_risk_ticket_outranks_low_risk(low_risk_ticket, high_risk_ticket):
    low = score_ticket(low_risk_ticket)
    high = score_ticket(high_risk_ticket)
    assert high["score"] > low["score"]
    assert high["risk_level"] == "High"
    assert low["risk_level"] == "Low"


def test_every_rule_produces_one_reason(high_risk_ticket):
    """Explainability guarantee: one plain-English reason per rule."""
    result = score_ticket(high_risk_ticket)
    assert len(result["reasons"]) == len(SCORING_RULES)
    assert all(isinstance(reason, str) and reason for reason in result["reasons"])


def test_resolved_status_reduces_score():
    """The same ticket should score lower once it is resolved."""
    base = {
        "category": "Hate Speech",
        "content_type": "Video",
        "status": "Open",
        "age_days": 10.0,
    }
    open_score = score_ticket(base)["score"]
    resolved_score = score_ticket({**base, "status": "Resolved"})["score"]
    assert resolved_score < open_score


def test_sensitive_unresolved_ticket_needs_escalation():
    assert needs_escalation_flag(
        {"category": "Self-Harm", "status": "Open"}
    ) is True


def test_resolved_sensitive_ticket_does_not_need_escalation():
    assert needs_escalation_flag(
        {"category": "Self-Harm", "status": "Resolved"}
    ) is False


def test_spam_does_not_auto_escalate():
    assert needs_escalation_flag(
        {"category": "Spam", "status": "Open"}
    ) is False
