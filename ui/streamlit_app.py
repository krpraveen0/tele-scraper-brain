from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.config import load_settings
from app.creator_studio_ui import render_creator_studio_v2
from app.export_archive_ui import render_export_archive_workflow
from app.models import StoredAsset, StoredSignal
from app.publishing_queue_ui import render_publishing_queue
from app.quality_gate_ui import render_quality_gate_dashboard
from app.storage import SignalStore
from app.telegram_client import TelegramSignalClient
from app.ui_navigation import (
    ASSET_WORKSPACE_TABS,
    BRIEFING_FEEDBACK_TABS,
    CREATOR_WORKSPACE_TABS,
    TOP_LEVEL_TABS,
    navigation_summary,
)
from app.ui_services import (
    add_feedback_label,
    allowed_asset_types,
    allowed_feedback_labels,
    build_action_brief,
    build_profile,
    create_asset_result,
    dashboard_snapshot,
    list_signals,
    signal_table_rows,
)


st.set_page_config(page_title="Praveen Signal OS", page_icon="🧠", layout="wide")

QUICK_FEEDBACK_ACTIONS = [
    ("Useful", "useful", "Useful signal"),
    ("Not useful", "not_useful", "Too generic or noisy"),
    ("Career", "career_opportunity", "Career opportunity"),
    ("LinkedIn", "linkedin_idea", "Can become a LinkedIn post"),
    ("Teaching", "teaching_example", "Can be used in class"),
    ("Research", "research_note", "Worth deeper research"),
    ("Tool", "tool_to_try", "Tool or repo worth trying"),
    ("English", "english_practice", "Useful for speaking practice"),
]

QUICK_ASSET_ACTIONS = [
    ("LinkedIn post", "linkedin"),
    ("Medium outline", "medium_outline"),
    ("Teaching example", "teaching_example"),
    ("Career note", "career_note"),
    ("English practice", "english_practice"),
    ("Research note", "research_note"),
    ("Tool review", "tool_review"),
]


@st.cache_resource
def get_runtime() -> tuple[object, SignalStore]:
    settings = load_settings()
    return settings, SignalStore(settings.database_path)


def main() -> None:
    st.title("Praveen Signal OS")
    st.caption("Local dashboard for signals, creator workflows, quality gates, exports, feedback, assets, briefings, and source intelligence.")

    try:
        settings, store = get_runtime()
    except Exception as exc:  # noqa: BLE001
        st.error("Could not load app settings. Check your `.env` values and sources config.")
        st.exception(exc)
        return

    tabs = st.tabs(TOP_LEVEL_TABS)

    with tabs[0]:
        render_dashboard(store)
    with tabs[1]:
        render_signals_inbox(settings, store)
    with tabs[2]:
        render_creator_workspace(settings, store)
    with tabs[3]:
        render_assets_workspace(settings, store)
    with tabs[4]:
        render_briefings_feedback_workspace(settings, store)


def render_dashboard(store: SignalStore) -> None:
    snapshot = dashboard_snapshot(store)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total signals", snapshot.total_signals)
    col2.metric("Valuable", snapshot.valuable_signals)
    col3.metric("Unsent", snapshot.unsent_signals)
    col4.metric("Assets", snapshot.recent_assets)
    col5.metric("Feedback labels", snapshot.feedback_labels)

    st.subheader("Main actions")
    c1, c2, c3, c4 = st.columns(4)
    c1.info("1. Review new signals")
    c2.info("2. Create in Creator Workspace")
    c3.info("3. Generate or review assets")
    c4.info("4. Brief and learn from feedback")

    st.subheader("Workspace map")
    st.table(navigation_summary())

    left, right = st.columns(2)
    with left:
        st.subheader("Top categories")
        if snapshot.top_categories:
            st.table([{"category": name, "count": count} for name, count in snapshot.top_categories])
        else:
            st.info("No category data yet. Run backfill or monitor first.")

    with right:
        st.subheader("Top sources")
        if snapshot.top_sources:
            st.table([{"source": name, "count": count} for name, count in snapshot.top_sources])
        else:
            st.info("No source data yet. Run backfill or monitor first.")


def render_creator_workspace(settings: object, store: SignalStore) -> None:
    st.subheader("Creator Workspace")
    st.caption("Create, check, queue, export, and archive creator outputs from one place.")
    tabs = st.tabs(CREATOR_WORKSPACE_TABS)

    with tabs[0]:
        render_creator_studio_v2(store)
    with tabs[1]:
        render_quality_gate_dashboard()
    with tabs[2]:
        render_publishing_queue(settings.database_path)  # type: ignore[attr-defined]
    with tabs[3]:
        render_export_archive_workflow(settings.asset_export_dir)  # type: ignore[attr-defined]


def render_assets_workspace(settings: object, store: SignalStore) -> None:
    st.subheader("Assets")
    st.caption("Generate reusable assets and review saved asset history.")
    tabs = st.tabs(ASSET_WORKSPACE_TABS)

    with tabs[0]:
        render_asset_studio(settings, store)
    with tabs[1]:
        render_assets(settings, store)


def render_briefings_feedback_workspace(settings: object, store: SignalStore) -> None:
    st.subheader("Briefings & Feedback")
    st.caption("Turn recent signals and feedback labels into operating intelligence.")
    tabs = st.tabs(BRIEFING_FEEDBACK_TABS)

    with tabs[0]:
        render_briefings(settings, store)
    with tabs[1]:
        render_feedback_profile(store)


def render_signals_inbox(settings: object, store: SignalStore) -> None:
    st.subheader("Signals Inbox")
    view = st.radio("View", ["Unsent", "Recent sent", "All"], horizontal=True)
    limit = st.slider("Limit", min_value=10, max_value=300, value=50, step=10, key="signals_limit")
    min_score = st.slider("Minimum score", min_value=0.0, max_value=10.0, value=0.0, step=0.5)
    category_filter = st.text_input("Category filter", placeholder="Example: AI Engineering")

    signals = list_signals(store, view=view, limit=limit)
    if category_filter.strip():
        signals = [item for item in signals if category_filter.strip().lower() in item.analysis.category.lower()]
    signals = [item for item in signals if item.analysis.score >= min_score]

    if not signals:
        st.info("No signals match the selected filters.")
        return

    st.dataframe(signal_table_rows(signals), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Action Center")
    selected_id = st.selectbox("Signal ID", [signal.id for signal in signals], key="signal_action_id")
    signal = store.get_signal(int(selected_id))
    if not signal:
        st.warning("Selected signal could not be loaded.")
        return

    render_signal_card(signal)
    render_quick_feedback(store, signal)
    render_quick_assets(settings, store, signal)


def render_signal_card(signal: StoredSignal) -> None:
    st.markdown(f"**{signal.analysis.category}** | score `{signal.analysis.score:.1f}` | source `{signal.source_title}`")
    st.write(signal.analysis.summary or signal.analysis.reason or signal.message_text[:500])
    if signal.permalink:
        st.link_button("Open source", signal.permalink)
    with st.expander("Original message"):
        st.write(signal.message_text)


def render_quick_feedback(store: SignalStore, signal: StoredSignal) -> None:
    st.markdown("### Quick feedback")
    for start in range(0, len(QUICK_FEEDBACK_ACTIONS), 4):
        columns = st.columns(4)
        for column, (text, label, note) in zip(columns, QUICK_FEEDBACK_ACTIONS[start : start + 4]):
            if column.button(text, key=f"feedback_{signal.id}_{label}"):
                try:
                    message = add_feedback_label(store, signal.id, label, note)
                    st.success(message)
                    st.cache_resource.clear()
                except Exception as exc:  # noqa: BLE001
                    st.error(str(exc))

    with st.expander("Custom feedback"):
        label = st.selectbox("Feedback label", allowed_feedback_labels(), key=f"custom_label_{signal.id}")
        notes = st.text_input("Notes", key=f"custom_notes_{signal.id}")
        if st.button("Save custom feedback", key=f"save_custom_{signal.id}"):
            try:
                message = add_feedback_label(store, signal.id, label, notes)
                st.success(message)
                st.cache_resource.clear()
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))


def render_quick_assets(settings: object, store: SignalStore, signal: StoredSignal) -> None:
    st.markdown("### Quick asset generation")
    save_asset = st.checkbox("Save asset", value=True, key=f"save_asset_{signal.id}")
    export_asset = st.checkbox("Export Markdown", value=False, key=f"export_asset_{signal.id}")
    rewrite_asset = st.checkbox("Rewrite with LLM", value=False, key=f"rewrite_asset_{signal.id}")

    for start in range(0, len(QUICK_ASSET_ACTIONS), 4):
        columns = st.columns(4)
        for column, (text, asset_type) in zip(columns, QUICK_ASSET_ACTIONS[start : start + 4]):
            if column.button(text, key=f"asset_{signal.id}_{asset_type}"):
                try:
                    result = create_asset_result(
                        settings=settings,
                        store=store,
                        signal_id=signal.id,
                        asset_type=asset_type,
                        rewrite=rewrite_asset,
                        save=save_asset,
                        export=export_asset,
                    )
                    st.success(f"Generated {asset_type} asset.")
                    if result.stored_asset:
                        st.info(f"Saved asset ID: {result.stored_asset.id}")
                    if result.exported_path:
                        st.info(f"Exported: {result.exported_path}")
                    st.markdown(result.asset.render())
                    st.cache_resource.clear()
                except Exception as exc:  # noqa: BLE001
                    st.error(str(exc))


def render_asset_studio(settings: object, store: SignalStore) -> None:
    st.subheader("Generate Asset")
    signals = list_signals(store, view="All", limit=200)
    if not signals:
        st.info("No saved signals yet. Run backfill or monitor first.")
        return

    col1, col2 = st.columns([1, 1])
    with col1:
        signal_id = st.selectbox("Signal ID", [signal.id for signal in signals], key="asset_signal_id")
        asset_type = st.selectbox("Asset type", allowed_asset_types(), key="asset_type")
        rewrite = st.checkbox("Rewrite with LLM", value=False)
        save = st.checkbox("Save to SQLite", value=True)
        export = st.checkbox("Export Markdown", value=False)
        export_dir = st.text_input("Export directory", value=str(getattr(settings, "asset_export_dir", Path("assets"))))

    with col2:
        signal = store.get_signal(int(signal_id))
        if signal:
            render_signal_card(signal)

    if st.button("Generate asset", type="primary"):
        try:
            result = create_asset_result(
                settings=settings,
                store=store,
                signal_id=int(signal_id),
                asset_type=asset_type,
                rewrite=rewrite,
                save=save,
                export=export,
                export_dir=export_dir if export else None,
            )
            st.success("Asset generated.")
            if result.stored_asset:
                st.info(f"Saved asset ID: {result.stored_asset.id}")
            if result.exported_path:
                st.info(f"Exported: {result.exported_path}")
            st.markdown(result.asset.render())
            st.cache_resource.clear()
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))


def render_briefings(settings: object, store: SignalStore) -> None:
    st.subheader("Daily Brief")
    hours = st.slider("Lookback hours", min_value=1, max_value=168, value=24)
    limit = st.slider("Signal limit", min_value=10, max_value=300, value=60, step=10, key="brief_limit")

    c1, c2 = st.columns(2)
    if c1.button("Generate daily action brief", type="primary"):
        brief = build_action_brief(store, hours=hours, limit=limit)
        st.session_state["last_action_brief"] = brief
    if c2.button("Refresh feedback profile"):
        st.session_state["feedback_profile"] = build_profile(store, limit=200)
        st.success("Feedback profile refreshed. Open the Feedback Profile tab.")

    brief_text = st.session_state.get("last_action_brief", "")
    if brief_text:
        st.markdown(brief_text)
        if st.button("Send brief to Telegram"):
            try:
                asyncio.run(send_text_to_telegram(settings, brief_text))
                st.success("Brief sent to Telegram.")
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))


def render_feedback_profile(store: SignalStore) -> None:
    st.subheader("Feedback Intelligence Profile")
    limit = st.slider("Profile scan limit", min_value=20, max_value=1000, value=200, step=20)
    if st.button("Generate feedback profile", type="primary"):
        st.session_state["feedback_profile"] = build_profile(store, limit=limit)
    profile = st.session_state.get("feedback_profile", "")
    if profile:
        st.markdown(profile)
    else:
        st.info("Generate the profile after adding useful/not useful labels.")


def render_assets(settings: object, store: SignalStore) -> None:
    st.subheader("Asset History")
    limit = st.slider("Asset limit", min_value=10, max_value=300, value=50, step=10, key="asset_limit")
    assets = store.recent_assets(limit=limit)
    if not assets:
        st.info("No generated assets yet.")
        return

    st.dataframe(asset_rows(assets), use_container_width=True, hide_index=True)
    selected_asset_id = st.selectbox("Asset ID", [asset.id for asset in assets], key="asset_history_id")
    asset = store.get_asset(int(selected_asset_id))
    if asset:
        st.markdown(asset.render())
        if st.button("Send asset to Telegram"):
            try:
                asyncio.run(send_asset_to_telegram(settings, store, asset))
                st.success("Asset sent to Telegram.")
                st.cache_resource.clear()
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))


def asset_rows(assets: list[StoredAsset]) -> list[dict[str, object]]:
    return [
        {
            "id": asset.id,
            "signal_id": asset.signal_id,
            "type": asset.asset_type,
            "rewritten": asset.rewritten,
            "exported_path": asset.exported_path,
            "sent": asset.sent_to_telegram,
            "created_at": asset.created_at,
            "title": asset.title,
        }
        for asset in assets
    ]


async def send_text_to_telegram(settings: object, text: str) -> None:
    telegram = TelegramSignalClient(settings)  # type: ignore[arg-type]
    await telegram.start()
    try:
        await telegram.send_briefing(text)
    finally:
        await telegram.disconnect()


async def send_asset_to_telegram(settings: object, store: SignalStore, asset: StoredAsset) -> None:
    telegram = TelegramSignalClient(settings)  # type: ignore[arg-type]
    await telegram.start()
    try:
        await telegram.send_asset(asset)
        store.mark_asset_sent(asset.id)
    finally:
        await telegram.disconnect()


if __name__ == "__main__":
    main()
