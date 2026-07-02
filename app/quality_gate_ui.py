from __future__ import annotations

import streamlit as st

from app.quality_gate import quality_rows, run_quality_gate
from app.voice_profile import ALLOWED_VOICE_SURFACES


def render_quality_gate_dashboard() -> None:
    st.subheader("Quality Gate")
    st.caption("Check whether a draft is practical, human, structured, and close to Praveen's voice before publishing.")

    col1, col2 = st.columns([2, 1])
    with col1:
        draft = st.text_area(
            "Draft to review",
            height=260,
            placeholder="Paste a LinkedIn post, Medium outline, course module, podcast script, or story draft here.",
            key="quality_gate_draft",
        )
    with col2:
        surface = st.selectbox("Surface", sorted(ALLOWED_VOICE_SURFACES), index=sorted(ALLOWED_VOICE_SURFACES).index("general"))
        st.info("This gate is deterministic. It does not call an LLM and does not publish anything.")

    if st.button("Run Quality Gate", type="primary"):
        report = run_quality_gate(draft, surface=surface)
        st.session_state["quality_gate_report"] = report

    report = st.session_state.get("quality_gate_report")
    if not report:
        st.info("Paste a draft and run the gate to see readiness, voice score, and improvement checks.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall score", f"{report.overall_score:.1f}/10")
    c2.metric("Voice score", f"{report.voice_review.score:.1f}/10")
    c3.metric("Passed checks", report.passed_checks)
    c4.metric("Failed checks", report.failed_checks)

    if report.ready_to_publish:
        st.success("Ready to publish or move forward.")
    else:
        st.warning("Needs revision before publishing.")

    st.dataframe(quality_rows(report), use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.markdown("### Voice strengths")
        if report.voice_review.strengths:
            for item in report.voice_review.strengths:
                st.success(item)
        else:
            st.info("No strengths detected yet.")

    with right:
        st.markdown("### Revision suggestions")
        if report.voice_review.suggestions:
            for item in report.voice_review.suggestions:
                st.warning(item)
        else:
            st.info("No suggestions available.")

    with st.expander("Copy-friendly Quality Gate report"):
        st.code(report.render(), language="markdown")
