from __future__ import annotations

from pathlib import Path

from app.intake_scheduler import IntakeSchedulerStore, build_intake_command, scheduler_job_rows


def test_build_intake_commands() -> None:
    assert build_intake_command("telegram backfill", limit_count=10) == "python -m app.main backfill --limit 10"
    assert build_intake_command("rss_backfill", limit_count=5, send_to_telegram=True) == "python -m app.rss_cli backfill --feeds feeds.yaml --limit 5 --send"
    assert build_intake_command("rss full article backfill", limit_count=3) == "python -m app.rss_cli backfill --feeds feeds.yaml --limit 3 --fetch-articles"


def test_create_list_and_rows(tmp_path: Path) -> None:
    store = IntakeSchedulerStore(tmp_path / "test.db")
    job = store.create_job(
        name="RSS every four hours",
        intake_type="rss_backfill",
        interval_hours=4,
        limit_count=12,
        send_to_telegram=True,
        next_run_at="2026-07-02T10:00:00+00:00",
    )

    jobs = store.list_jobs()
    rows = scheduler_job_rows(jobs)

    assert jobs[0].id == job.id
    assert jobs[0].name == "RSS every four hours"
    assert jobs[0].interval_hours == 4
    assert jobs[0].send_to_telegram is True
    assert rows[0]["command"] == "python -m app.rss_cli backfill --feeds feeds.yaml --limit 12 --send"


def test_due_jobs_only_returns_enabled_due_items(tmp_path: Path) -> None:
    store = IntakeSchedulerStore(tmp_path / "test.db")
    due = store.create_job("Due", "telegram_backfill", 2, next_run_at="2026-07-02T10:00:00+00:00")
    store.create_job("Future", "rss_backfill", 2, next_run_at="2026-07-02T15:00:00+00:00")
    store.create_job("Disabled", "rss_backfill", 2, enabled=False, next_run_at="2026-07-02T09:00:00+00:00")

    jobs = store.due_jobs(now="2026-07-02T12:00:00+00:00")

    assert [job.id for job in jobs] == [due.id]


def test_mark_run_advances_next_run(tmp_path: Path) -> None:
    store = IntakeSchedulerStore(tmp_path / "test.db")
    job = store.create_job("Telegram", "telegram_backfill", 6, next_run_at="2026-07-02T10:00:00+00:00")

    updated = store.mark_run(job.id, run_at="2026-07-02T12:00:00+00:00")

    assert updated.last_run_at == "2026-07-02T12:00:00+00:00"
    assert updated.next_run_at == "2026-07-02T18:00:00+00:00"


def test_set_enabled_and_delete_job(tmp_path: Path) -> None:
    store = IntakeSchedulerStore(tmp_path / "test.db")
    job = store.create_job("Telegram", "telegram_backfill", 2)

    disabled = store.set_enabled(job.id, False)
    assert disabled.enabled is False

    store.delete_job(job.id)
    assert store.get_job(job.id) is None
