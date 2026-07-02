from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.intake_scheduler import IntakeSchedulerStore
from app.intake_scheduler_runner import (
    due_job_rows,
    run_due_scheduler_jobs,
    run_scheduler_job_by_id,
    scheduler_result_rows,
)


@dataclass(frozen=True)
class FakeCompleted:
    returncode: int = 0
    stdout: str = "ok"
    stderr: str = ""


def test_run_due_scheduler_jobs_marks_successful_jobs_as_run(tmp_path: Path) -> None:
    store = IntakeSchedulerStore(tmp_path / "test.db")
    job = store.create_job("Due", "telegram_backfill", 3, next_run_at="2026-07-02T10:00:00+00:00")

    results = run_due_scheduler_jobs(
        store,
        now="2026-07-02T12:00:00+00:00",
        command_runner=lambda command: FakeCompleted(),  # type: ignore[arg-type]
    )

    updated = store.get_job(job.id)
    assert len(results) == 1
    assert results[0].succeeded is True
    assert results[0].marked_run is True
    assert updated is not None
    assert updated.last_run_at is not None


def test_failed_scheduler_job_is_not_marked_run(tmp_path: Path) -> None:
    store = IntakeSchedulerStore(tmp_path / "test.db")
    job = store.create_job("Due", "telegram_backfill", 3, next_run_at="2026-07-02T10:00:00+00:00")

    results = run_due_scheduler_jobs(
        store,
        now="2026-07-02T12:00:00+00:00",
        command_runner=lambda command: FakeCompleted(returncode=1, stderr="boom"),  # type: ignore[arg-type]
    )

    updated = store.get_job(job.id)
    assert results[0].succeeded is False
    assert results[0].marked_run is False
    assert updated is not None
    assert updated.last_run_at is None


def test_dry_run_does_not_execute_or_mark_run(tmp_path: Path) -> None:
    store = IntakeSchedulerStore(tmp_path / "test.db")
    job = store.create_job("Due", "rss_backfill", 3, next_run_at="2026-07-02T10:00:00+00:00")

    result = run_scheduler_job_by_id(store, job.id, dry_run=True)
    updated = store.get_job(job.id)

    assert result.dry_run is True
    assert result.marked_run is False
    assert "dry-run" in result.stdout
    assert updated is not None
    assert updated.last_run_at is None


def test_due_job_rows_and_result_rows_are_ui_friendly(tmp_path: Path) -> None:
    store = IntakeSchedulerStore(tmp_path / "test.db")
    store.create_job("Due", "telegram_backfill", 3, next_run_at="2026-07-02T10:00:00+00:00")

    due_rows = due_job_rows(store, now="2026-07-02T12:00:00+00:00")
    results = run_due_scheduler_jobs(
        store,
        now="2026-07-02T12:00:00+00:00",
        command_runner=lambda command: FakeCompleted(stdout="done"),  # type: ignore[arg-type]
    )
    result_rows = scheduler_result_rows(results)

    assert due_rows[0]["due"] is True
    assert result_rows[0]["succeeded"] is True
    assert result_rows[0]["stdout"] == "done"
