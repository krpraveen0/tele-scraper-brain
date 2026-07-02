from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.export_archive import ALLOWED_EXPORT_TYPES, ExportableContent, archive_content, export_content_to_markdown


def render_export_archive_workflow(default_export_dir: Path) -> None:
    st.subheader("Export & Archive")
    st.caption("Export drafts to Markdown or archive content into date-based folders. This does not publish or call an LLM.")

    export_tab, archive_tab = st.tabs(["Export Markdown", "Archive Content"])
    with export_tab:
        render_export_tab(default_export_dir)
    with archive_tab:
        render_archive_tab(default_export_dir)


def render_export_tab(default_export_dir: Path) -> None:
    st.markdown("### Export Markdown")
    content = collect_content_form(prefix="export")
    export_dir = Path(st.text_input("Export directory", value=str(default_export_dir), key="export_dir"))

    if st.button("Export Markdown", type="primary", key="export_markdown_button"):
        try:
            path = export_content_to_markdown(content, export_dir)
            st.success(f"Exported Markdown: {path}")
            st.session_state["last_export_path"] = str(path)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))


def render_archive_tab(default_export_dir: Path) -> None:
    st.markdown("### Archive Content")
    content = collect_content_form(prefix="archive")
    archive_root = Path(st.text_input("Archive root", value=str(default_export_dir / "archive"), key="archive_root"))
    reason = st.text_input("Archive reason", value="Completed or moved out of active workflow.", key="archive_reason")

    if st.button("Archive Content", type="primary", key="archive_content_button"):
        try:
            record = archive_content(content, archive_root, reason=reason)
            st.success(f"Archived: {record.path}")
            st.session_state["last_archive_record"] = record.render()
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    record_text = st.session_state.get("last_archive_record", "")
    if record_text:
        with st.expander("Last archive record"):
            st.code(record_text, language="markdown")


def collect_content_form(prefix: str) -> ExportableContent:
    title = st.text_input("Title", key=f"{prefix}_title")
    content_type = st.selectbox("Content type", sorted(ALLOWED_EXPORT_TYPES), key=f"{prefix}_content_type")
    source_id_value = st.number_input("Optional source ID", min_value=0, value=0, step=1, key=f"{prefix}_source_id")
    body = st.text_area("Markdown body", height=260, key=f"{prefix}_body")
    return ExportableContent(
        title=title,
        body=body,
        content_type=content_type,
        source_id=int(source_id_value) or None,
        metadata={"created_from": "streamlit_export_archive"},
    )
