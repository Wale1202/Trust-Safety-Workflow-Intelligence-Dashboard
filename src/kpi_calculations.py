"""
KPI calculations for the operations dashboard.

All functions take a tickets DataFrame (as produced by ``database.load_tickets``
and optionally enriched by ``risk_scoring.score_dataframe``) and return plain
numbers or small aggregated DataFrames. Keeping the maths here -- away from the
Streamlit UI -- makes each metric easy to unit test and easy to explain.
"""

from __future__ import annotations

import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Return the headline KPI numbers shown as metric cards."""
    total = len(df)
    open_tickets = int((df["status"] == "Open").sum())
    in_review = int((df["status"] == "In Review").sum())
    resolved = int((df["status"] == "Resolved").sum())
    escalated = int((df["status"] == "Escalated").sum())

    # High-risk depends on the risk_level column being present.
    if "risk_level" in df.columns:
        high_risk = int((df["risk_level"] == "High").sum())
    else:
        high_risk = int((df["priority"] == "High").sum())

    avg_resolution = df["resolution_time_hours"].dropna().mean()
    avg_resolution = round(float(avg_resolution), 1) if pd.notna(avg_resolution) else 0.0

    escalation_rate = round((escalated / total) * 100, 1) if total else 0.0

    # Backlog = anything not resolved (still consuming team capacity).
    backlog = int((df["status"] != "Resolved").sum())

    resolution_rate = round((resolved / total) * 100, 1) if total else 0.0

    return {
        "total_tickets": total,
        "open_tickets": open_tickets,
        "in_review_tickets": in_review,
        "resolved_tickets": resolved,
        "escalated_tickets": escalated,
        "high_risk_tickets": high_risk,
        "avg_resolution_hours": avg_resolution,
        "escalation_rate_pct": escalation_rate,
        "resolution_rate_pct": resolution_rate,
        "backlog_count": backlog,
    }


def tickets_by_category(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("category").size().reset_index(name="count").sort_values("count", ascending=False)
    )


def tickets_by_status(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("status").size().reset_index(name="count")


def tickets_by_priority(df: pd.DataFrame) -> pd.DataFrame:
    order = ["Low", "Medium", "High"]
    out = df.groupby("priority").size().reset_index(name="count")
    out["priority"] = pd.Categorical(out["priority"], categories=order, ordered=True)
    return out.sort_values("priority")


def tickets_by_region(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("region").size().reset_index(name="count").sort_values("count", ascending=False)
    )


def resolution_time_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Average resolution time (hours) per category, resolved tickets only."""
    resolved = df.dropna(subset=["resolution_time_hours"])
    if resolved.empty:
        return pd.DataFrame(columns=["category", "avg_hours"])
    out = (
        resolved.groupby("category")["resolution_time_hours"]
        .mean()
        .round(1)
        .reset_index(name="avg_hours")
        .sort_values("avg_hours", ascending=False)
    )
    return out
