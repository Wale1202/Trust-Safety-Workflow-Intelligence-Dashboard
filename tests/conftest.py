"""
Shared test fixtures.

A couple of small, hand-built ticket dicts so the tests don't depend on the
database or the synthetic CSV -- the logic is what we want to verify, in
isolation.
"""

import pytest


@pytest.fixture
def low_risk_ticket() -> dict:
    """Resolved spam comment: should land at the bottom of the risk range."""
    return {
        "ticket_id": "TS-0001",
        "category": "Spam",
        "content_type": "Comment",
        "status": "Resolved",
        "region": "Europe",
        "age_days": 1.0,
        "short_description": "Account posting the same promotional link.",
    }


@pytest.fixture
def high_risk_ticket() -> dict:
    """Old, unresolved child-safety live stream: should be clearly High."""
    return {
        "ticket_id": "TS-0002",
        "category": "Child Safety",
        "content_type": "Live Stream",
        "status": "Escalated",
        "region": "APAC",
        "age_days": 30.0,
        "short_description": "Profile flagged for a routine minor-safety review.",
    }
