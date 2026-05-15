"""
Page 1 — Ticket Dashboard
=========================

The operational core: a filterable table of moderation tickets plus the KPI
section (metric cards + charts). Everything reads from SQLite via the database
module and is risk-scored on the fly.
"""

import plotly.express as px
import streamlit as st

from src.database import load_tickets
from src.kpi_calculations import (
    compute_kpis,
    resolution_time_by_category,
    tickets_by_category,
    tickets_by_priority,
    tickets_by_region,
    tickets_by_status,
)
from src.risk_scoring import score_dataframe

st.set_page_config(page_title="Ticket Dashboard", page_icon="📋", layout="wide")

st.title("📋 Ticket Dashboard")
st.caption("Filter the synthetic moderation queue and monitor workflow KPIs.")

# --------------------------------------------------------------------------- #
# Load + enrich data
# --------------------------------------------------------------------------- #
df = score_dataframe(load_tickets())

# --------------------------------------------------------------------------- #
# Sidebar filters
# --------------------------------------------------------------------------- #
st.sidebar.header("🔎 Filters")


def _multi(label, column):
    options = sorted(df[column].dropna().unique().tolist())
    return st.sidebar.multiselect(label, options, default=options)


sel_status = _multi("Status", "status")
sel_category = _multi("Category", "category")
sel_priority = _multi("Priority", "priority")
sel_team = _multi("Assigned Team", "assigned_team")
sel_content = _multi("Content Type", "content_type")
sel_region = _multi("Region", "region")

filtered = df[
    df["status"].isin(sel_status)
    & df["category"].isin(sel_category)
    & df["priority"].isin(sel_priority)
    & df["assigned_team"].isin(sel_team)
    & df["content_type"].isin(sel_content)
    & df["region"].isin(sel_region)
]

if filtered.empty:
    st.warning("No tickets match the current filters. Widen the selection.")
    st.stop()

# --------------------------------------------------------------------------- #
# KPI cards
# --------------------------------------------------------------------------- #
kpis = compute_kpis(filtered)

st.subheader("Key Performance Indicators")
r1 = st.columns(4)
r1[0].metric("Total Tickets", kpis["total_tickets"])
r1[1].metric("Open", kpis["open_tickets"])
r1[2].metric("Resolved", kpis["resolved_tickets"])
r1[3].metric("Escalated", kpis["escalated_tickets"])

r2 = st.columns(4)
r2[0].metric("High Risk", kpis["high_risk_tickets"])
r2[1].metric("Avg Resolution (hrs)", kpis["avg_resolution_hours"])
r2[2].metric("Escalation Rate", f"{kpis['escalation_rate_pct']}%")
r2[3].metric("Backlog", kpis["backlog_count"])

st.divider()

# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
st.subheader("Workflow Analytics")

col_a, col_b = st.columns(2)

with col_a:
    cat = tickets_by_category(filtered)
    fig = px.bar(
        cat, x="count", y="category", orientation="h",
        title="Tickets by Category", text="count",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=380)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    stat = tickets_by_status(filtered)
    fig = px.pie(stat, names="status", values="count", title="Tickets by Status", hole=0.45)
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

col_c, col_d = st.columns(2)

with col_c:
    pri = tickets_by_priority(filtered)
    fig = px.bar(
        pri, x="priority", y="count", title="Tickets by Priority",
        color="priority",
        color_discrete_map={"Low": "#2ca02c", "Medium": "#ff7f0e", "High": "#d62728"},
        text="count",
    )
    fig.update_layout(height=360, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    reg = tickets_by_region(filtered)
    fig = px.bar(reg, x="region", y="count", title="Tickets by Region", text="count")
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)

res = resolution_time_by_category(filtered)
if not res.empty:
    fig = px.bar(
        res, x="avg_hours", y="category", orientation="h",
        title="Avg Resolution Time by Category (resolved tickets, hours)",
        text="avg_hours",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=380)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No resolved tickets in the current filter to chart resolution time.")

st.divider()

# --------------------------------------------------------------------------- #
# Ticket table
# --------------------------------------------------------------------------- #
st.subheader(f"Ticket Queue ({len(filtered)} shown)")

display_cols = [
    "ticket_id", "category", "content_type", "priority", "status",
    "risk_level", "risk_score", "assigned_team", "region",
    "age_days", "resolution_time_hours", "short_description",
]

st.dataframe(
    filtered[display_cols].sort_values("risk_score", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "risk_score": st.column_config.ProgressColumn(
            "Risk Score", min_value=0, max_value=100, format="%d"
        ),
        "short_description": st.column_config.TextColumn("Description", width="large"),
    },
)

st.download_button(
    "⬇️ Download filtered tickets (CSV)",
    data=filtered[display_cols].to_csv(index=False).encode("utf-8"),
    file_name="filtered_tickets.csv",
    mime="text/csv",
)
