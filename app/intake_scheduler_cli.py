from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table

from app.config import load_settings
from app.intake_scheduler import IntakeSchedulerStore, scheduler_job_rows
from app.intake_scheduler_runner import run_due_scheduler_jobs, run_scheduler_job_by_id, scheduler_result_rows

console = Console()


def scheduler_store(database_path: str | None = None) -> IntakeSchedulerStore:
    if database_path:
        return IntakeSchedulerStore(Path(database_path))
    settings = load_settings()
    return IntakeSchedulerStore(settings.database_path)


def print_jobs(rows: list[dict[str, object]], title: str) -> None:
    table = Table(title=title)
    table.add_column("ID", justify="right")
    table.add_column("Enabled")
    table.add_column("Due")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Next run")
    table.add_column("Command")
    for row in rows:
        table.add_row(
            str(row["id"]),
            "yes" if row["enabled"] else "no",
            "yes" if row["due"] else "no",
            str(row["name"]),
            str(row["type"]),
            str(row["next_run_at"]),
            str(row["command"]),
        )
    console.print(table)


def print_results(rows: list[dict[str, object]], title: str) -> None:
    table = Table(title=title)
    table.add_column("Job ID", justify="right")
    table.add_column("Name")
    table.add_column("OK")
    table.add_column("Code", justify="right")
    table.add_column("Dry run")
    table.add_column("Marked run")
    table.add_column("Command")
    for row in rows:
        table.add_row(
            str(row["job_id"]),
            str(row["job_name"]),
            "yes" if row["succeeded"] else "no",
            str(row["returncode"]),
            "yes" if row["dry_run"] else "no",
            "yes" if row["marked_run"] else "no",
            str(row["command"]),
        )
    console.print(table)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run due intake scheduler jobs")
    parser.add_argument("--database", default="", help="Optional SQLite database path. Defaults to settings database_path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List saved scheduler jobs")
    list_parser.add_argument("--enabled-only", action="store_true", help="Show only enabled jobs")
    list_parser.add_argument("--limit", type=int, default=100)

    due_parser = subparsers.add_parser("due", help="List due scheduler jobs")
    due_parser.add_argument("--limit", type=int, default=20)

    run_due_parser = subparsers.add_parser("run-due", help="Run due scheduler jobs once")
    run_due_parser.add_argument("--limit", type=int, default=20)
    run_due_parser.add_argument("--dry-run", action="store_true")

    run_one_parser = subparsers.add_parser("run-one", help="Run one scheduler job by ID")
    run_one_parser.add_argument("job_id", type=int)
    run_one_parser.add_argument("--dry-run", action="store_true")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    store = scheduler_store(args.database or None)

    if args.command == "list":
        rows = scheduler_job_rows(store.list_jobs(include_disabled=not args.enabled_only, limit=args.limit))
        print_jobs(rows, "Saved intake schedules")
        return

    if args.command == "due":
        rows = scheduler_job_rows(store.due_jobs(limit=args.limit))
        print_jobs(rows, "Due intake schedules")
        return

    if args.command == "run-due":
        results = run_due_scheduler_jobs(store, limit=args.limit, dry_run=args.dry_run)
        print_results(scheduler_result_rows(results), "Scheduler run results")
        return

    if args.command == "run-one":
        result = run_scheduler_job_by_id(store, args.job_id, dry_run=args.dry_run)
        print_results(scheduler_result_rows([result]), "Scheduler run result")
        return

    raise RuntimeError(f"Unsupported scheduler command: {args.command}")


if __name__ == "__main__":
    main()
