"""
Page 2 — AI Ticket Review
=========================

Select a ticket, then see:
  * an AI-style structured summary (local rule-based, or LLM if configured)
  * an explainable risk score with the full reasoning trail

This is the page that demonstrates "AI workflow + explainability" thinking.
"""

import streamlit as st

from src.ai_summary import generate_summary, is_llm_enabled
from src.database import load_tickets
from src.risk_scoring import score_ticket

st.set_page_config(page_title="AI Ticket Review", page_icon="🤖", layout="wide")

st.title("🤖 AI Ticket Review")
st.caption("AI-assisted summary + explainable risk score for a single ticket.")

if is_llm_enabled():
    st.success("LLM mode available (API key detected). Local fallback still active.")
else:
    st.info("Running in local rule-based mode — no API key required.")

df = load_tickets()

# --------------------------------------------------------------------------- #
# Ticket picker
# --------------------------------------------------------------------------- #
col1, col2 = st.columns([1, 2])

with col1:
    category_filter = st.selectbox(
        "Filter by category (optional)",
        ["All"] + sorted(df["category"].unique().tolist()),
    )

scoped = df if category_filter == "All" else df[df["category"] == category_filter]

# The dropdown stores ticket IDs directly and only formats the label for
# display, so we never have to parse a string back into an ID.
ticket_lookup = scoped.set_index("ticket_id")


def _format_ticket(ticket_id: str) -> str:
    row = ticket_lookup.loc[ticket_id]
    return f"{ticket_id} · {row['category']} · {row['status']}"


with col2:
    selected_id = st.selectbox(
        "Select a ticket",
        options=scoped["ticket_id"].tolist(),
        format_func=_format_ticket,
    )

ticket = df[df["ticket_id"] == selected_id].iloc[0].to_dict()

st.divider()

# --------------------------------------------------------------------------- #
# Raw ticket details
# --------------------------------------------------------------------------- #
st.subheader(f"Ticket {ticket['ticket_id']}")

d1, d2, d3, d4 = st.columns(4)
d1.metric("Category", ticket["category"])
d2.metric("Priority", ticket["priority"])
d3.metric("Status", ticket["status"])
age = ticket.get("age_days")
d4.metric("Age (days)", f"{age:.0f}" if age is not None else "—")

st.markdown(
    f"**Content type:** {ticket['content_type']}  ·  "
    f"**Region:** {ticket['region']}  ·  "
    f"**Assigned team:** {ticket['assigned_team']}"
)
st.markdown(f"**Description:** {ticket['short_description']}")

st.divider()

# --------------------------------------------------------------------------- #
# AI summary
# --------------------------------------------------------------------------- #
st.subheader("🧾 AI-Assisted Summary")

if st.button("Generate summary", type="primary"):
    with st.spinner("Generating summary..."):
        summary = generate_summary(ticket)

    st.caption(f"Source: `{summary['source']}`")

    st.markdown("**Short summary**")
    st.write(summary["short_summary"])

    st.markdown("**Likely user issue**")
    st.write(summary["likely_issue"])

    st.markdown("**Suggested next action**")
    st.success(summary["next_action"])

    st.markdown("**Escalation recommendation**")
    if summary["escalation_recommendation"].startswith("ESCALATE"):
        st.error(summary["escalation_recommendation"])
    else:
        st.info(summary["escalation_recommendation"])
else:
    st.caption("Click **Generate summary** to produce the AI-style write-up.")

st.divider()

# --------------------------------------------------------------------------- #
# Explainable risk score
# --------------------------------------------------------------------------- #
st.subheader("📊 Explainable Risk Score")

risk = score_ticket(ticket)

rc1, rc2 = st.columns([1, 2])
with rc1:
    st.metric("Risk Score", f"{risk['score']} / 100")
    badge = {"High": "🔴 High", "Medium": "🟠 Medium", "Low": "🟢 Low"}[risk["risk_level"]]
    st.metric("Risk Level", badge)
    st.progress(risk["score"] / 100)

with rc2:
    st.markdown("**Why this score? (full reasoning trail)**")
    for reason in risk["reasons"]:
        st.markdown(f"- {reason}")

st.caption(
    "The score is a transparent additive rule model — no black box. Every "
    "point is attributed to a named, defensible signal."
)
