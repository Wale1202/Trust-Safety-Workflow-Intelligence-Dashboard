"""
Tests for the KPI calculations.

A tiny hand-built DataFrame with known values means we can assert the exact
numbers -- if a KPI definition silently changes, these fail.
"""

import pandas as pd

from src.kpi_calculations import compute_kpis, tickets_by_status


def _sample_df() -> pd.DataFrame:
    """4 tickets: 1 Open, 1 In Review, 1 Escalated, 1 Resolved (12h)."""
    return pd.DataFrame(
        [
            {"status": "Open", "priority": "Low", "resolution_time_hours": None, "category": "Spam", "region": "Europe", "risk_level": "Low"},
            {"status": "In Review", "priority": "Medium", "resolution_time_hours": None, "category": "Spam", "region": "APAC", "risk_level": "Medium"},
            {"status": "Escalated", "priority": "High", "resolution_time_hours": None, "category": "Self-Harm", "region": "APAC", "risk_level": "High"},
            {"status": "Resolved", "priority": "High", "resolution_time_hours": 12.0, "category": "Hate Speech", "region": "Europe", "risk_level": "High"},
        ]
    )


def test_headline_counts_are_correct():
    kpis = compute_kpis(_sample_df())
    assert kpis["total_tickets"] == 4
    assert kpis["open_tickets"] == 1
    assert kpis["resolved_tickets"] == 1
    assert kpis["escalated_tickets"] == 1
    assert kpis["high_risk_tickets"] == 2  # two rows have risk_level High


def test_backlog_is_everything_not_resolved():
    kpis = compute_kpis(_sample_df())
    assert kpis["backlog_count"] == 3


def test_rates_and_averages():
    kpis = compute_kpis(_sample_df())
    assert kpis["escalation_rate_pct"] == 25.0  # 1 of 4
    assert kpis["resolution_rate_pct"] == 25.0  # 1 of 4
    assert kpis["avg_resolution_hours"] == 12.0  # only the resolved ticket


def test_empty_dataframe_does_not_crash():
    empty = _sample_df().iloc[0:0]
    kpis = compute_kpis(empty)
    assert kpis["total_tickets"] == 0
    assert kpis["escalation_rate_pct"] == 0.0


def test_tickets_by_status_groups_all_rows():
    grouped = tickets_by_status(_sample_df())
    assert grouped["count"].sum() == 4
