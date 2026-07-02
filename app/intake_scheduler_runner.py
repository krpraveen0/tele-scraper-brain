from __future__ import annotations

from dataclasses import dataclass
import subprocess
from typing import Callable

from app.intake_scheduler import IntakeSchedulerJob, IntakeSchedulerStore, scheduler_job_rows


@dataclass(frozen=True)
class SchedulerRunResult:
    job_id: int
    job_name: str
    command: str
    returncode: int
    stdout: str
    stderr: str
    dry_run: bool = False
    marked_run: bool = False

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def run_scheduler_command(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command.split(),
        check=False,
        capture_output=True,
        text=True,
        timeout=900,
    )


def run_scheduler_job(
    store: IntakeSchedulerStore,
    job: IntakeSchedulerJob,
    dry_run: bool = False,
    command_runner: Callable[[str], subprocess.CompletedProcess[str]] = run_scheduler_command,
) -> SchedulerRunResult:
    if dry_run:
        return SchedulerRunResult(
            job_id=job.id,
            job_name=job.name,
            command=job.command,
            returncode=0,
            stdout="dry-run: command not executed",
            stderr="",
            dry_run=True,
            marked_run=False,
        )

    completed = command_runner(job.command)
    marked = False
    if completed.returncode == 0:
        store.mark_run(job.id)
        marked = True
    return SchedulerRunResult(
        job_id=job.id,
        job_name=job.name,
        command=job.command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        dry_run=False,
        marked_run=marked,
    )


def run_due_scheduler_jobs(
    store: IntakeSchedulerStore,
    now: str | None = None,
    limit: int = 20,
    dry_run: bool = False,
    command_runner: Callable[[str], subprocess.CompletedProcess[str]] = run_scheduler_command,
) -> list[SchedulerRunResult]:
    jobs = store.due_jobs(now=now, limit=limit)
    return [run_scheduler_job(store, job, dry_run=dry_run, command_runner=command_runner) for job in jobs]


def run_scheduler_job_by_id(
    store: IntakeSchedulerStore,
    job_id: int,
    dry_run: bool = False,
    command_runner: Callable[[str], subprocess.CompletedProcess[str]] = run_scheduler_command,
) -> SchedulerRunResult:
    job = store.get_job(job_id)
    if job is None:
        raise ValueError(f"Scheduler job {job_id} does not exist.")
    return run_scheduler_job(store, job, dry_run=dry_run, command_runner=command_runner)


def scheduler_result_rows(results: list[SchedulerRunResult]) -> list[dict[str, object]]:
    return [
        {
            "job_id": result.job_id,
            "job_name": result.job_name,
            "succeeded": result.succeeded,
            "returncode": result.returncode,
            "dry_run": result.dry_run,
            "marked_run": result.marked_run,
            "command": result.command,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
        for result in results
    ]


def due_job_rows(store: IntakeSchedulerStore, now: str | None = None, limit: int = 20) -> list[dict[str, object]]:
    return scheduler_job_rows(store.due_jobs(now=now, limit=limit))
