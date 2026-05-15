"""
Page 4 — Platform Guide
=======================

A plain-language enablement guide for operations users: how to review tickets,
read risk scores, use AI summaries and KPIs, the escalation process, and
responsible-AI limitations.
"""

import streamlit as st

st.set_page_config(page_title="Platform Guide", page_icon="📖", layout="wide")

st.title("📖 Platform Guide")
st.caption("How a Trust & Safety operations user would work with this dashboard.")

st.markdown(
    """
This guide is written for moderation analysts and team leads. It explains the
*workflow*, not just the buttons — the kind of enablement documentation a
technical product / ops role is expected to produce.
"""
)

with st.expander("1. How to review tickets", expanded=True):
    st.markdown(
        """
- Open **Ticket Dashboard**.
- Use the sidebar filters (status, category, priority, team, content type,
  region) to narrow to your queue.
- The table is **sorted by risk score** so the most urgent work is at the top.
- Start with **Escalated** and **High risk** items, then **Open** by age.
- Use the CSV download to share a working subset with a colleague.
"""
    )

with st.expander("2. How to interpret risk scores"):
    st.markdown(
        """
- Each ticket gets a **0–100 score** and a **Low / Medium / High** band.
- The score is a **transparent additive rule model**, not a black box.
- It combines: category sensitivity, content reach, ticket age (if unresolved),
  status, and whether escalation is implied.
- On **AI Ticket Review** you can see the **full reasoning trail** — every
  point is attributed to a named signal, so you can defend any decision.
- Treat the score as **decision support**, not an automatic action.
"""
    )

with st.expander("3. How to use AI summaries"):
    st.markdown(
        """
- Go to **AI Ticket Review**, pick a ticket, click **Generate summary**.
- You get: a short summary, the likely user issue, a suggested next action,
  and an escalation recommendation.
- Without an API key it runs a **local rule-based** summariser (fully offline).
- With an `OPENAI_API_KEY` it uses an LLM, falling back automatically on error.
- Always **read the underlying ticket** — the summary speeds you up, it does
  not replace reviewer judgement.
"""
    )

with st.expander("4. How to use KPI insights"):
    st.markdown(
        """
- The KPI cards show total / open / resolved / escalated / high-risk volumes,
  average resolution time, escalation rate, and backlog.
- **Backlog + average resolution time** together tell you if the team is
  keeping pace.
- A rising **escalation rate** may signal a policy gap or a brigading event —
  raise it with a team lead.
- Charts by category / region help spot where to rebalance staffing.
"""
    )

with st.expander("5. Escalation process"):
    st.markdown(
        """
1. A ticket is flagged for escalation when it is a **sensitive category**
   (Child Safety, Self-Harm, Hate Speech) and **not yet resolved**, or it is
   already marked **Escalated**.
2. Route escalated tickets to **Safety Escalations** (or Legal & Compliance
   for legal exposure).
3. Add the relevant policy checklist and request a **second reviewer** for
   high-risk actions.
4. Record the outcome so resolution-time KPIs stay accurate.
"""
    )

with st.expander("6. Limitations & responsible-AI notes", expanded=True):
    st.markdown(
        """
- **All data is synthetic.** No real users, no real or graphic content.
- This is a **portfolio / learning simulation**, not a production moderation
  system. Do not connect it to live user data.
- The risk model is **rule-based and explainable by design** — that is a
  feature, because moderation decisions must be auditable.
- AI summaries can be **wrong or incomplete**; they are decision *support*.
  A human reviewer is always accountable for the final action.
- Sensitive categories are handled at a **policy/workflow** level here — the
  app deliberately contains no graphic descriptions.
- Any real deployment would additionally need: reviewer wellbeing safeguards,
  bias review of scoring weights, audit logging, and access controls.
"""
    )

st.divider()
st.caption("Synthetic demo — Trust & Safety Workflow Intelligence Dashboard.")
