from __future__ import annotations

import subprocess
import sys

import streamlit as st

from app.config import Settings
from app.intake_scheduler import ALLOWED_INTAKE_JOB_TYPES, IntakeSchedulerStore, scheduler_job_rows
from app.source_intake import (
    command_rows,
    configured_feed_rows,
    configured_source_rows,
    feed_candidate_rows,
    intake_commands,
    scheduler_snippets,
    source_quality_rows,
    source_recommendation_rows,
)
from app.storage import SignalStore


def render_source_intake(settings: Settings, store: SignalStore) -> None:
    st.subheader("Source Intake")
    st.caption("Fetch Telegram and RSS/blog signals, understand source quality, prepare scheduling, and discover useful sources.")

    tabs = st.tabs(["Fetch Now", "Configured Sources", "Source Quality", "Scheduling", "Feed Candidates"])
    with tabs[0]:
        render_fetch_now()
    with tabs[1]:
        render_configured_sources(settings)
    with tabs[2]:
        render_source_quality(store)
    with tabs[3]:
        render_scheduling(settings)
    with tabs[4]:
        render_feed_candidates()


def render_fetch_now() -> None:
    st.markdown("### Fetch Signals")
    st.write("Run one-time intake commands for Telegram or RSS/blog feeds. Commands use the existing local CLI paths under the hood.")

    limit = st.slider("Items per source", min_value=1, max_value=200, value=20, step=5, key="intake_backfill_limit")
    send = st.checkbox("Forward saved signals to Telegram destination", value=False, key="intake_backfill_send")
    commands = intake_commands(limit=limit, send=send)
    command_titles = [command.title for command in commands]
    selected_title = st.selectbox("Command", command_titles, key="intake_command_title")
    selected_command = next(command for command in commands if command.title == selected_title)

    st.code(selected_command.command, language="bash")
    st.info(selected_command.purpose)
    st.warning("For first-time Telegram login/OTP, run the Telegram command in your terminal first. Streamlit is best after the session is already authenticated.")

    if st.button("Run Selected Intake Command", type="primary", key="run_selected_intake_command"):
        result = run_command(selected_command.command)
        if result.returncode == 0:
            st.success("Intake command completed.")
        else:
            st.error(f"Intake command failed with exit code {result.returncode}.")
        if result.stdout:
            st.text_area("Output", result.stdout, height=240)
        if result.stderr:
            st.text_area("Errors", result.stderr, height=160)

    st.markdown("### Useful intake commands")
    st.dataframe(command_rows(commands), use_container_width=True, hide_index=True)


def render_configured_sources(settings: Settings) -> None:
    st.markdown("### Configured Telegram Sources")
    st.write(f"Telegram config file: `{settings.sources_config_path}`")
    rows = configured_source_rows(settings)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No configured Telegram sources found. Add Telegram channels/groups to sources.yaml or SOURCE_CHATS.")

    st.markdown("### Configured RSS/blog Feeds")
    feeds_path = st.text_input("Feeds config path", value="feeds.yaml", key="feeds_config_path")
    st.write("Feed-specific `min_save_score` and `destination` are active during RSS backfill.")
    try:
        feed_rows = configured_feed_rows(feeds_path)
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))
        feed_rows = []

    if feed_rows:
        st.dataframe(feed_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No configured RSS/blog feeds found. Copy feeds.example.yaml to feeds.yaml and edit it.")
    st.code(f"python -m app.rss_cli feeds --feeds {feeds_path}", language="bash")


def render_source_quality(store: SignalStore) -> None:
    st.markdown("### Source Quality")
    stats = source_quality_rows(store)
    if stats:
        st.dataframe(stats, use_container_width=True, hide_index=True)
    else:
        st.info("No source stats yet. Run a Telegram or RSS/blog backfill first.")

    min_samples = st.slider("Minimum samples for recommendations", min_value=1, max_value=100, value=10, step=1)
    recommendations = source_recommendation_rows(store, min_samples=min_samples)
    if recommendations:
        st.markdown("### Tuning Recommendations")
        st.dataframe(recommendations, use_container_width=True, hide_index=True)
    else:
        st.info("No recommendations yet. Collect more data first.")


def render_scheduling(settings: Settings) -> None:
    st.markdown("### Scheduling")
    st.caption("Store intake schedules in SQLite and run due commands when you are ready. This does not install a background daemon.")
    scheduler_store = IntakeSchedulerStore(settings.database_path)

    saved_tab, snippets_tab = st.tabs(["Saved schedules", "Command snippets"])
    with saved_tab:
        render_saved_schedules(scheduler_store)
    with snippets_tab:
        render_scheduler_snippets()


def render_saved_schedules(scheduler_store: IntakeSchedulerStore) -> None:
    with st.form("create_intake_schedule"):
        st.markdown("#### Create schedule")
        name = st.text_input("Name", value="RSS/blog backfill")
        intake_type = st.selectbox("Intake type", sorted(ALLOWED_INTAKE_JOB_TYPES), index=1)
        interval_hours = st.number_input("Run every N hours", min_value=1, max_value=720, value=4, step=1)
        limit_count = st.number_input("Items per source", min_value=1, max_value=500, value=20, step=5)
        feeds_path = st.text_input("Feeds path", value="feeds.yaml")
        send_to_telegram = st.checkbox("Forward saved signals to Telegram destination", value=False)
        enabled = st.checkbox("Enable schedule", value=True)
        submitted = st.form_submit_button("Save schedule")

    if submitted:
        try:
            job = scheduler_store.create_job(
                name=name,
                intake_type=intake_type,
                interval_hours=int(interval_hours),
                limit_count=int(limit_count),
                send_to_telegram=send_to_telegram,
                feeds_path=feeds_path,
                enabled=enabled,
            )
            st.success(f"Saved schedule #{job.id}: {job.name}")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    jobs = scheduler_store.list_jobs()
    due_jobs = scheduler_store.due_jobs()

    st.markdown("#### Saved schedules")
    if jobs:
        st.dataframe(scheduler_job_rows(jobs), use_container_width=True, hide_index=True)
    else:
        st.info("No saved schedules yet.")

    if due_jobs:
        st.warning(f"{len(due_jobs)} schedule(s) are due. Select a job below to run or mark it as run.")
    else:
        st.info("No schedules are due right now.")

    if not jobs:
        return

    selected_id = st.selectbox("Select job", [job.id for job in jobs], key="scheduler_selected_job")
    selected_job = scheduler_store.get_job(int(selected_id))
    if not selected_job:
        st.warning("Selected schedule could not be loaded.")
        return

    st.code(selected_job.command, language="bash")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Run command now", key=f"run_schedule_{selected_job.id}"):
        result = run_command(selected_job.command)
        if result.returncode == 0:
            scheduler_store.mark_run(selected_job.id)
            st.success("Command completed and schedule marked as run.")
        else:
            st.error(f"Command failed with exit code {result.returncode}.")
        if result.stdout:
            st.text_area("Scheduler output", result.stdout, height=220)
        if result.stderr:
            st.text_area("Scheduler errors", result.stderr, height=160)

    if c2.button("Mark as run", key=f"mark_schedule_{selected_job.id}"):
        updated = scheduler_store.mark_run(selected_job.id)
        st.success(f"Marked as run. Next run: {updated.next_run_at}")

    if c3.button("Enable/Disable", key=f"toggle_schedule_{selected_job.id}"):
        updated = scheduler_store.set_enabled(selected_job.id, not selected_job.enabled)
        st.success(f"Schedule is now {'enabled' if updated.enabled else 'disabled'}.")

    if c4.button("Delete", key=f"delete_schedule_{selected_job.id}"):
        scheduler_store.delete_job(selected_job.id)
        st.success("Schedule deleted.")

    with st.expander("Copy-friendly schedule record"):
        st.code(selected_job.render(), language="markdown")


def render_scheduler_snippets() -> None:
    limit = st.slider("Scheduled backfill limit", min_value=1, max_value=200, value=20, step=5, key="scheduler_limit")
    snippets = scheduler_snippets(limit=limit)

    st.write("Use these as starting points for cron, launchd, or a small always-on terminal process.")
    for title, command in snippets.items():
        st.markdown(f"**{title}**")
        st.code(command, language="bash")

    st.info("The app currently generates scheduler commands; it does not install OS-level cron/launchd jobs for you.")


def render_feed_candidates() -> None:
    st.markdown("### Blog / Feed Candidates")
    st.write("These are high-signal candidates for your AI engineering, training, research, product, and content workflows.")
    st.dataframe(feed_candidate_rows(), use_container_width=True, hide_index=True)
    st.success("RSS/blog ingestion backend is available. Add selected feed URLs to feeds.yaml, then run `python -m app.rss_cli backfill --feeds feeds.yaml --limit 10`.")


def run_command(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command.split(),
        check=False,
        capture_output=True,
        text=True,
        timeout=900,
        cwd=None,
    )
