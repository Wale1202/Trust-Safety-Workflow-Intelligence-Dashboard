"""
Page 3 — BRD / MRD Generator
============================

Paste messy stakeholder notes; get a structured Business / Market Requirements
Document with the standard PM sections, plus a downloadable Markdown file.
"""

import streamlit as st

from src.brd_generator import (
    SECTION_ORDER,
    SECTION_TITLES,
    generate_brd,
    to_markdown,
)

st.set_page_config(page_title="BRD / MRD Generator", page_icon="📝", layout="wide")

st.title("📝 BRD / MRD Generator")
st.caption(
    "Turn unstructured stakeholder notes into a structured product document."
)

SAMPLE = (
    "moderators say triage is super slow and inconsistent\n"
    "we need a dashboard to see open vs resolved tickets\n"
    "should be able to filter by category and region\n"
    "leadership wants to track escalation rate and avg resolution time\n"
    "must not use any real user data, privacy is critical\n"
    "risk: rule scoring might need tuning when policy changes\n"
    "users are T&S analysts and team leads\n"
    "needs to be fast and easy for new grads to learn"
)

doc_title = st.text_input("Document title", "Trust & Safety Dashboard — PRD")

notes = st.text_area(
    "Paste messy stakeholder notes here",
    value=SAMPLE,
    height=220,
    help="Bullet points, half sentences, anything. The generator will structure it.",
)

if st.button("Generate BRD / MRD", type="primary"):
    if not notes.strip():
        st.warning("Please enter some notes first.")
        st.stop()

    brd = generate_brd(notes, title=doc_title)
    st.caption(f"Source: `{brd['source']}` · Generated {brd['generated_on']}")

    st.divider()
    for key in SECTION_ORDER:
        st.subheader(SECTION_TITLES[key])
        items = brd["sections"].get(key, [])
        if not items:
            st.caption("_None captured._")
        for item in items:
            st.markdown(f"- {item}")

    st.divider()
    md = to_markdown(brd)
    st.download_button(
        "⬇️ Download as Markdown",
        data=md.encode("utf-8"),
        file_name="brd_mrd.md",
        mime="text/markdown",
    )

    with st.expander("Preview raw Markdown"):
        st.code(md, language="markdown")
else:
    st.info(
        "Edit the notes above (a sample is pre-filled) and click "
        "**Generate BRD / MRD**."
    )
