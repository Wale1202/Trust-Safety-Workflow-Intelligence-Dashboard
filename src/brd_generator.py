"""
BRD / MRD generator.

Turns messy, free-form stakeholder notes into a structured Business / Market
Requirements Document.

How it works: split the notes into individual statements, then route each
statement into the most relevant section using a small keyword map. Any
section the notes didn't cover is filled from a defaults table so the document
is never half-empty. The two checklists are standardised on purpose.

Like the summary module, this is rule-based by default. The optional LLM only
rewrites the Business Problem into a tighter narrative -- the requirements,
metrics, and checklists stay rule-based so the document is reproducible.
"""

from __future__ import annotations

import os
import re
from datetime import date
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Sections in the order they appear in the final document.
SECTION_ORDER = [
    "business_problem",
    "user_pain_points",
    "target_users",
    "functional_requirements",
    "non_functional_requirements",
    "key_metrics",
    "risks_and_assumptions",
    "launch_checklist",
    "test_checklist",
]

SECTION_TITLES = {
    "business_problem": "1. Business Problem",
    "user_pain_points": "2. User Pain Points",
    "target_users": "3. Target Users",
    "functional_requirements": "4. Functional Requirements",
    "non_functional_requirements": "5. Non-Functional Requirements",
    "key_metrics": "6. Key Metrics / KPIs",
    "risks_and_assumptions": "7. Risks & Assumptions",
    "launch_checklist": "8. Launch Checklist",
    "test_checklist": "9. Test / Verification Checklist",
}

# A statement is routed to the first section whose keywords it matches.
SECTION_KEYWORDS = {
    "user_pain_points": ["pain", "frustrat", "slow", "confus", "hard", "annoy", "complain", "struggl"],
    "target_users": ["user", "moderator", "analyst", "team", "operator", "stakeholder", "customer", "audience"],
    "functional_requirements": ["need", "should", "must", "feature", "able to", "support", "allow", "build", "add"],
    "non_functional_requirements": ["fast", "secure", "scal", "perform", "reliab", "uptime", "privacy", "latency", "accessib"],
    "key_metrics": ["metric", "kpi", "measure", "rate", "%", "reduce", "increase", "target", "sla", "track"],
    "risks_and_assumptions": ["risk", "assume", "depend", "if ", "maybe", "uncertain", "concern", "block"],
}

# Used to fill any section the notes did not cover, so the doc is complete.
SECTION_DEFAULTS = {
    "target_users": ["Trust & Safety operations analysts and moderation team leads."],
    "non_functional_requirements": [
        "Responsive UI (under ~2s typical page load).",
        "No real user PII; synthetic data only.",
        "Explainable, auditable decision logic.",
    ],
    "key_metrics": [
        "Average resolution time (hours).",
        "Escalation rate (%).",
        "Backlog count and aging.",
    ],
    "risks_and_assumptions": [
        "Assumes incoming ticket data is reasonably well-structured.",
        "Risk: rule-based scoring may need tuning when policy changes.",
    ],
    "user_pain_points": ["Manual triage is slow and inconsistent across reviewers."],
    "functional_requirements": ["Provide a filterable ticket dashboard with KPI metrics."],
}

# Standardised regardless of the notes -- these are always the same checks.
LAUNCH_CHECKLIST = [
    "Stakeholders have reviewed and approved this document.",
    "Synthetic data validated; no real or harmful content present.",
    "Risk scoring thresholds reviewed with a policy owner.",
    "Dashboard KPIs match agreed definitions.",
    "Rollback / fallback plan documented.",
]
TEST_CHECKLIST = [
    "App starts with `streamlit run app.py` and no errors.",
    "All filters return correct subsets on the Ticket Dashboard.",
    "Risk score reasons render for a sample of tickets.",
    "AI summary works with and without an API key.",
    "BRD/MRD export downloads valid Markdown.",
]


def _split_into_statements(raw: str) -> list[str]:
    """Break free-form notes into individual statements.

    Splits on newlines, semicolons, bullets and sentence ends, then drops
    fragments too short to be meaningful.
    """
    parts = re.split(r"[\n;]+|(?<=[.!?])\s+|\s*[-*•]\s+", raw.strip())
    return [p.strip(" -*•\t").strip() for p in parts if len(p.strip()) > 2]


def _section_for(statement: str) -> str:
    """Pick the section a statement belongs to (functional reqs as default)."""
    text = statement.lower()
    for section, keywords in SECTION_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return section
    return "functional_requirements"


def _business_problem(statements: list[str]) -> list[str]:
    """Summarise the business problem from the first couple of statements."""
    if not statements:
        return ["No notes provided."]
    summary = " ".join(statements[:2])
    if len(statements) > 2:
        summary += " ..."
    return [f"Derived from stakeholder notes: {summary}"]


def generate_brd(notes: str, title: str = "Product Requirements Document") -> dict[str, Any]:
    """Build the structured BRD/MRD from raw notes.

    Returns a dict with title, date, source, and a ``sections`` map.
    """
    statements = _split_into_statements(notes)

    sections: dict[str, list[str]] = {key: [] for key in SECTION_ORDER}
    for statement in statements:
        sections[_section_for(statement)].append(statement)

    sections["business_problem"] = _business_problem(statements)

    # Fill anything the notes didn't cover so no section is left empty.
    for key, default in SECTION_DEFAULTS.items():
        if not sections[key]:
            sections[key] = default

    sections["launch_checklist"] = LAUNCH_CHECKLIST
    sections["test_checklist"] = TEST_CHECKLIST

    source = "local-rule-based"
    llm_problem = _llm_business_problem(notes)
    if llm_problem:
        sections["business_problem"] = [llm_problem]
        source = f"llm:{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')} (problem only)"

    return {
        "title": title,
        "generated_on": date.today().isoformat(),
        "source": source,
        "sections": sections,
    }


def _llm_business_problem(notes: str) -> str | None:
    """Optional: use the LLM to rewrite ONLY the business problem narrative.

    Returns None (keep the rule-based text) if no key is set or the call fails.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a senior product manager."},
                {
                    "role": "user",
                    "content": (
                        "From these messy stakeholder notes, write a tight "
                        "2-3 sentence Business Problem statement only.\n\n"
                        f"{notes}"
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        print(f"[brd_generator] LLM call failed, using local text: {exc}")
        return None


def to_markdown(brd: dict[str, Any]) -> str:
    """Render the structured BRD dict as downloadable Markdown."""
    lines = [
        f"# {brd['title']}",
        "",
        f"*Generated on {brd['generated_on']} — source: {brd['source']}*",
        "",
        "> Synthetic demo document produced by the Trust & Safety Workflow "
        "Intelligence Dashboard.",
        "",
    ]
    for key in SECTION_ORDER:
        lines.append(f"## {SECTION_TITLES[key]}")
        lines.append("")
        items = brd["sections"].get(key) or ["_None captured._"]
        lines.extend(f"- {item}" for item in items)
        lines.append("")
    return "\n".join(lines)
