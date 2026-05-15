"""
AI-style ticket summary generator.

The summary always has the same four parts: a short summary, the likely user
issue, a suggested next action, and an escalation recommendation.

By default everything is produced by a deterministic rule-based function, so
the project runs with no API key. If an OpenAI key is configured, the LLM is
used for ONE thing only -- rewriting the short summary into more natural prose.
The next action and escalation recommendation always stay rule-based, because
those are the parts that have to be explainable and auditable.

That split is the key design point: AI improves readability, not the decision.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from src.risk_scoring import needs_escalation_flag, score_ticket

load_dotenv()

# Suggested next action per category. Operational and deliberately non-graphic.
NEXT_ACTIONS = {
    "Child Safety": "Route to the Child Safety specialist queue and apply the age-verification workflow.",
    "Self-Harm": "Attach the wellbeing resource template and route to the trained Safety Escalations team.",
    "Hate Speech": "Apply the hate-speech policy checklist and request a second reviewer before action.",
    "Bullying / Harassment": "Review interaction history between the accounts and consider a temporary interaction limit.",
    "Misinformation": "Send to the fact-check queue and label as pending verification.",
    "Animal Harm": "Apply the animal-welfare policy review and request more context from the reporter.",
    "Spam": "Apply the bulk-action spam rule and check the account for automated behaviour.",
}


def _local_summary(ticket: dict[str, Any]) -> dict[str, str]:
    """Build the full four-part summary using rules only. No API needed."""
    category = str(ticket.get("category", "Unknown"))
    content_type = str(ticket.get("content_type", "content")).lower()
    status = str(ticket.get("status", "Open"))
    region = str(ticket.get("region", "an unspecified region"))
    description = str(ticket.get("short_description", "")).strip().rstrip(".")

    age = ticket.get("age_days")
    age_phrase = f"{age:.0f} days old" if isinstance(age, (int, float)) else "of unknown age"

    risk = score_ticket(ticket)

    short_summary = (
        f"A {content_type} ticket in '{category}' from {region}, "
        f"currently '{status}' and {age_phrase}. {description}."
    )
    likely_issue = (
        f"The reporter is likely concerned about a possible '{category}' "
        f"policy issue involving {content_type} content."
    )
    next_action = NEXT_ACTIONS.get(
        category, "Triage against the relevant policy checklist and assign an owner."
    )

    if needs_escalation_flag(ticket):
        escalation = (
            f"ESCALATE. Sensitive category ('{category}') still unresolved "
            f"(risk {risk['score']}/100, {risk['risk_level']}). "
            f"Route to a specialist team."
        )
    else:
        escalation = (
            f"No escalation required (risk {risk['score']}/100, "
            f"{risk['risk_level']}). Handle in the standard queue and watch for aging."
        )

    return {
        "short_summary": short_summary,
        "likely_issue": likely_issue,
        "next_action": next_action,
        "escalation_recommendation": escalation,
        "source": "local-rule-based",
    }


def _llm_short_summary(ticket: dict[str, Any]) -> str | None:
    """Optional: use the LLM to rewrite ONLY the short summary as prose.

    Returns None (so the caller keeps the rule-based text) if no key is set or
    the call fails for any reason.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI  # imported lazily; only needed if opted in

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        prompt = (
            "Summarise this moderation ticket for a reviewer in 2-3 concise, "
            "non-graphic sentences.\n"
            f"Category: {ticket.get('category')}\n"
            f"Content type: {ticket.get('content_type')}\n"
            f"Status: {ticket.get('status')}\n"
            f"Region: {ticket.get('region')}\n"
            f"Age (days): {ticket.get('age_days')}\n"
            f"Description: {ticket.get('short_description')}"
        )
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a concise Trust & Safety analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:  # any failure -> fall back to rule-based text
        print(f"[ai_summary] LLM call failed, using local summary: {exc}")
        return None


def generate_summary(ticket: dict[str, Any]) -> dict[str, str]:
    """Public entry point.

    Always builds the rule-based summary first, then (only if available) swaps
    in an LLM-written short summary. The decision-relevant fields are never
    touched by the LLM.
    """
    summary = _local_summary(ticket)

    llm_text = _llm_short_summary(ticket)
    if llm_text:
        summary["short_summary"] = llm_text
        summary["source"] = f"llm:{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')} (summary only)"

    return summary


def is_llm_enabled() -> bool:
    """True if an API key is configured (used by the UI to show the mode)."""
    return bool(os.getenv("OPENAI_API_KEY"))
