from __future__ import annotations

import streamlit as st

from app.creator_services import allowed_blueprint_types, create_blueprint
from app.models import StoredSignal
from app.storage import SignalStore
from app.ui_services import create_idea_lab_report, list_signals, signal_table_rows


def render_creator_studio_v2(store: SignalStore) -> None:
    st.subheader("Creator Studio")
    st.caption("Turn one strong signal into original writing, course, podcast, and story directions.")

    creator_tabs = st.tabs(["Idea Lab", "Blueprint Studio"])
    with creator_tabs[0]:
        render_idea_lab(store)
    with creator_tabs[1]:
        render_blueprint_studio(store)


def render_idea_lab(store: SignalStore) -> None:
    st.markdown("### Idea Lab")
    st.write("Select one saved signal and generate a deterministic Idea Lab report. This does not call an LLM or save anything yet.")

    signals = list_signals(store, view="All", limit=200)
    if not signals:
        st.info("No saved signals yet. Run backfill or monitor first.")
        return

    st.dataframe(signal_table_rows(signals), use_container_width=True, hide_index=True)
    selected_id = st.selectbox("Signal ID", [signal.id for signal in signals], key="idea_lab_signal_id")
    signal = store.get_signal(int(selected_id))
    if signal:
        render_signal_preview(signal)

    if st.button("Generate Idea Lab Report", type="primary", key="generate_idea_lab_report"):
        try:
            report = create_idea_lab_report(store, int(selected_id))
            st.session_state["last_idea_lab_report"] = report.render()
            st.success("Idea Lab report generated.")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    report_text = st.session_state.get("last_idea_lab_report", "")
    if report_text:
        st.markdown(report_text)
        with st.expander("Copy-friendly Markdown"):
            st.code(report_text, language="markdown")


def render_blueprint_studio(store: SignalStore) -> None:
    st.markdown("### Blueprint Studio")
    st.write("Convert one saved signal into a structured blueprint. This does not call an LLM or save anything yet.")

    signals = list_signals(store, view="All", limit=200)
    if not signals:
        st.info("No saved signals yet. Run backfill or monitor first.")
        return

    st.dataframe(signal_table_rows(signals), use_container_width=True, hide_index=True)
    selected_id = st.selectbox("Signal ID", [signal.id for signal in signals], key="blueprint_signal_id")
    blueprint_type = st.selectbox("Blueprint type", allowed_blueprint_types(), key="blueprint_type")

    signal = store.get_signal(int(selected_id))
    if signal:
        render_signal_preview(signal)

    if st.button("Generate Blueprint", type="primary", key="generate_blueprint"):
        try:
            blueprint = create_blueprint(store, int(selected_id), blueprint_type)
            st.session_state["last_blueprint"] = blueprint.render()
            st.success("Blueprint generated.")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    blueprint_text = st.session_state.get("last_blueprint", "")
    if blueprint_text:
        st.markdown(blueprint_text)
        with st.expander("Copy-friendly Markdown"):
            st.code(blueprint_text, language="markdown")


def render_signal_preview(signal: StoredSignal) -> None:
    st.markdown(f"**{signal.analysis.category}** | score `{signal.analysis.score:.1f}` | source `{signal.source_title}`")
    st.write(signal.analysis.summary or signal.analysis.reason or signal.message_text[:500])
    if signal.permalink:
        st.link_button("Open source", signal.permalink)
