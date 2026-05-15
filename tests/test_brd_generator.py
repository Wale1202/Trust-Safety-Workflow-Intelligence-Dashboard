"""
Tests for the BRD/MRD generator.

We check the *structure contract*: all nine sections are always present, no
section is empty, the standard checklists are fixed, and notes get routed to a
sensible section. The exact wording isn't asserted -- structure is what the
rest of the app and the Markdown export depend on.
"""

from src.brd_generator import (
    LAUNCH_CHECKLIST,
    SECTION_ORDER,
    generate_brd,
    to_markdown,
)


def test_all_sections_present_and_non_empty():
    brd = generate_brd("moderators say triage is slow; need a dashboard")
    assert list(brd["sections"].keys()) == SECTION_ORDER
    for section, items in brd["sections"].items():
        assert items, f"section '{section}' should not be empty"


def test_empty_notes_still_produces_valid_document():
    brd = generate_brd("")
    assert list(brd["sections"].keys()) == SECTION_ORDER
    assert brd["sections"]["business_problem"] == ["No notes provided."]


def test_checklists_are_standardised():
    brd = generate_brd("anything at all here")
    assert brd["sections"]["launch_checklist"] == LAUNCH_CHECKLIST


def test_notes_are_routed_to_relevant_sections():
    """Statements with a single clear signal land in the right section."""
    notes = "moderators are frustrated by slow triage; track escalation rate"
    brd = generate_brd(notes)
    pain = " ".join(brd["sections"]["user_pain_points"]).lower()
    metrics = " ".join(brd["sections"]["key_metrics"]).lower()
    assert "slow triage" in pain
    assert "escalation rate" in metrics


def test_router_is_first_match_wins():
    """Documents a known limitation of the simple heuristic: a statement that
    matches several buckets is filed under the first one checked (functional
    requirements outranks non-functional here because of the word 'must')."""
    brd = generate_brd("the system must be fast and secure")
    funcs = " ".join(brd["sections"]["functional_requirements"]).lower()
    assert "must be fast and secure" in funcs


def test_markdown_export_contains_every_section_heading():
    brd = generate_brd("need filtering by region")
    md = to_markdown(brd)
    assert md.startswith("# ")
    assert "## 1. Business Problem" in md
    assert "## 9. Test / Verification Checklist" in md


def test_default_source_is_local_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    brd = generate_brd("simple note")
    assert brd["source"] == "local-rule-based"
