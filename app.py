"""
Trust & Safety Workflow Intelligence Dashboard
==============================================

Home / landing page.

This is a synthetic, portfolio-style operations platform that simulates how a
Trust & Safety team would triage moderation tickets, monitor workflow KPIs,
generate AI-assisted ticket summaries, score risk in an explainable way, and
draft BRD/MRD product documentation.

Run locally with:

    streamlit run app.py

All data is fake. No real or graphic harmful content is included anywhere.
"""

import streamlit as st

from src.database import init_db
from src.kpi_calculations import compute_kpis
from src.risk_scoring import score_dataframe
from src.database import load_tickets
from src.ai_summary import is_llm_enabled

st.set_page_config(
    page_title="Trust & Safety Workflow Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide",
)

# Make sure the SQLite DB exists / is seeded before any page loads.
init_db()

st.title("🛡️ Trust & Safety Workflow Intelligence Dashboard")
st.caption(
    "A synthetic operations platform for moderation ticket triage, workflow "
    "analytics, explainable risk scoring, AI summaries, and product docs."
)

st.info(
    "**Demo / synthetic data only.** Every ticket here is fake and all "
    "descriptions are intentionally mild and non-graphic. This project "
    "simulates Trust & Safety operations for learning and portfolio use.",
    icon="ℹ️",
)

# ---- Quick health snapshot on the landing page --------------------------- #
df = score_dataframe(load_tickets())
kpis = compute_kpis(df)

st.subheader("Live Snapshot")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Tickets", kpis["total_tickets"])
c2.metric("Open / Backlog", kpis["backlog_count"])
c3.metric("Escalated", kpis["escalated_tickets"])
c4.metric("High Risk", kpis["high_risk_tickets"])

c5, c6, c7, c8 = st.columns(4)
c5.metric("Resolved", kpis["resolved_tickets"])
c6.metric("Avg Resolution (hrs)", kpis["avg_resolution_hours"])
c7.metric("Escalation Rate", f"{kpis['escalation_rate_pct']}%")
c8.metric("Resolution Rate", f"{kpis['resolution_rate_pct']}%")

st.divider()

# ---- Navigation guide ---------------------------------------------------- #
left, right = st.columns(2)

with left:
    st.subheader("📋 What's inside")
    st.markdown(
        """
- **Ticket Dashboard** — filterable ticket table + KPI metrics and charts.
- **AI Ticket Review** — pick a ticket and get an AI-style summary and an
  explainable risk score with reasoning.
- **BRD/MRD Generator** — paste messy stakeholder notes, get a structured,
  downloadable product document.
- **Platform Guide** — how operations users would actually use this tool,
  including escalation process and responsible-AI notes.

Use the **sidebar** to move between pages.
"""
    )

with right:
    st.subheader("🤖 AI mode")
    if is_llm_enabled():
        st.success(
            "An LLM API key was detected. AI summaries / BRD will use the API, "
            "with the local rule-based engine as a fallback."
        )
    else:
        st.warning(
            "No API key detected — running in **local rule-based mode**. "
            "Everything still works fully offline. Add `OPENAI_API_KEY` to a "
            "`.env` file to enable the optional LLM path."
        )
    st.subheader("🧠 Why this project")
    st.markdown(
        "It demonstrates product thinking, systems/ops workflow design, "
        "explainable AI logic, and documentation skills relevant to an "
        "early-career Trust & Safety / technical product role."
    )

st.divider()
st.caption(
    "Built with Python · Streamlit · SQLite · Pandas · Plotly. "
    "Synthetic data — not for production moderation use."
)
