"""
Explainable risk scoring for moderation tickets.

This is deliberately NOT a machine-learning model. In Trust & Safety you have
to be able to tell a reviewer, a manager, or an auditor exactly why a ticket
was prioritised the way it was. So the score is a simple sum of five rules,
and every rule returns the points it added *and* a plain-English reason.

The five rules: category sensitivity, content reach, ticket age, status, and
whether the ticket implies escalation. Each one lives in its own small
function below so it can be read, changed, and justified on its own.
"""

from __future__ import annotations

from typing import Any

# How sensitive each policy category is. Child Safety and Self-Harm score
# highest because the cost of a slow or missed response is highest.
CATEGORY_WEIGHTS = {
    "Child Safety": 45,
    "Self-Harm": 40,
    "Hate Speech": 30,
    "Bullying / Harassment": 22,
    "Misinformation": 18,
    "Animal Harm": 18,
    "Spam": 6,
}

# Content reach: a live stream or video spreads faster and wider than a DM.
CONTENT_TYPE_WEIGHTS = {
    "Live Stream": 14,
    "Video": 12,
    "Image": 9,
    "Text Post": 8,
    "Comment": 5,
    "Direct Message": 4,
}

# Categories sensitive enough that an unresolved ticket should be escalated.
SENSITIVE_CATEGORIES = {"Child Safety", "Self-Harm", "Hate Speech"}

# Total score -> risk band.
HIGH_THRESHOLD = 60
MEDIUM_THRESHOLD = 30


def _field(ticket: dict[str, Any], key: str) -> str:
    """Read a ticket field as a clean string (handles missing/None)."""
    return str(ticket.get(key, "") or "").strip()


# --------------------------------------------------------------------------- #
# The five scoring rules. Each takes the ticket and returns (points, reason).
# Keeping them separate is the whole point: any rule can be explained or
# re-tuned without touching the others.
# --------------------------------------------------------------------------- #

def _category_rule(ticket: dict[str, Any]) -> tuple[int, str]:
    """More sensitive policy categories add more points."""
    category = _field(ticket, "category")
    points = CATEGORY_WEIGHTS.get(category, 10)
    return points, f"Category '{category}' adds {points} (policy sensitivity)."


def _content_reach_rule(ticket: dict[str, Any]) -> tuple[int, str]:
    """Content that reaches more people faster adds more points."""
    content_type = _field(ticket, "content_type")
    points = CONTENT_TYPE_WEIGHTS.get(content_type, 6)
    return points, f"Content type '{content_type}' adds {points} (potential reach)."


def _age_rule(ticket: dict[str, Any]) -> tuple[int, str]:
    """An unresolved ticket gets riskier the longer it sits. Resolved tickets
    get no age penalty because the issue is already closed."""
    if _field(ticket, "status") == "Resolved":
        return 0, "Resolved ticket: no age penalty."

    age_days = ticket.get("age_days")
    if age_days is None:
        return 0, "Ticket age unknown: no age penalty."

    if age_days >= 14:
        return 20, f"Open {age_days:.0f} days (>=14) adds 20 (aging backlog)."
    if age_days >= 7:
        return 12, f"Open {age_days:.0f} days (>=7) adds 12."
    if age_days >= 3:
        return 6, f"Open {age_days:.0f} days (>=3) adds 6."
    return 0, f"Open {age_days:.0f} days (<3): no age penalty."


def _status_rule(ticket: dict[str, Any]) -> tuple[int, str]:
    """Where the ticket is in the workflow. Resolved subtracts points."""
    status = _field(ticket, "status")
    table = {
        "Escalated": (18, "Status 'Escalated' adds 18 (already flagged serious)."),
        "Open": (8, "Status 'Open' adds 8 (not yet triaged)."),
        "In Review": (4, "Status 'In Review' adds 4 (work in progress)."),
        "Resolved": (-15, "Status 'Resolved' subtracts 15 (issue closed)."),
    }
    return table.get(status, (0, f"Status '{status}': no adjustment."))


def _escalation_rule(ticket: dict[str, Any]) -> tuple[int, str]:
    """Sensitive-and-unresolved tickets imply escalation, which adds points."""
    if needs_escalation_flag(ticket):
        return 15, "Escalation recommended adds 15 (sensitive & unresolved)."
    return 0, "No escalation implied: no adjustment."


# The rules applied, in order. This list *is* the model.
SCORING_RULES = (
    _category_rule,
    _content_reach_rule,
    _age_rule,
    _status_rule,
    _escalation_rule,
)


def needs_escalation_flag(ticket: dict[str, Any]) -> bool:
    """Should this ticket go to a specialist team?

    True if it's already marked Escalated, or it's a sensitive category that
    is not yet resolved.
    """
    status = _field(ticket, "status")
    if status == "Escalated":
        return True
    category = _field(ticket, "category")
    return category in SENSITIVE_CATEGORIES and status != "Resolved"


def _risk_band(score: int) -> str:
    """Map a 0-100 score to a Low / Medium / High band."""
    if score >= HIGH_THRESHOLD:
        return "High"
    if score >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Low"


def score_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    """Score one ticket by summing the five rules.

    Returns:
        score:      int 0-100 (clamped)
        risk_level: "Low" | "Medium" | "High"
        reasons:    one plain-English line per rule (the audit trail)
    """
    score = 0
    reasons: list[str] = []
    for rule in SCORING_RULES:
        points, reason = rule(ticket)
        score += points
        reasons.append(reason)

    score = max(0, min(100, score))
    return {"score": score, "risk_level": _risk_band(score), "reasons": reasons}


def score_dataframe(df):
    """Add ``risk_score`` and ``risk_level`` columns to a tickets DataFrame.

    Returns a new DataFrame; the input is not modified.
    """
    scored = [score_ticket(row) for row in df.to_dict("records")]
    out = df.copy()
    out["risk_score"] = [s["score"] for s in scored]
    out["risk_level"] = [s["risk_level"] for s in scored]
    return out
