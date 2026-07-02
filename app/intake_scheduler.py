from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from typing import Any


ALLOWED_INTAKE_JOB_TYPES = {
    "telegram_backfill",
    "rss_backfill",
    "rss_full_article_backfill",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS intake_scheduler_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    intake_type TEXT NOT NULL,
    command TEXT NOT NULL,
    interval_hours INTEGER NOT NULL,
    limit_count INTEGER NOT NULL,
    send_to_telegram INTEGER NOT NULL DEFAULT 0,
    feeds_path TEXT NOT NULL DEFAULT 'feeds.yaml',
    enabled INTEGER NOT NULL DEFAULT 1,
    last_run_at TEXT,
    next_run_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_intake_scheduler_jobs_next_run
ON intake_scheduler_jobs(enabled, next_run_at);
"""


@dataclass(frozen=True)
class IntakeSchedulerJob:
    id: int
    name: str
    intake_type: str
    command: str
    interval_hours: int
    limit_count: int
    send_to_telegram: bool
    feeds_path: str
    enabled: bool
    last_run_at: str | None
    next_run_at: str
    created_at: str
    updated_at: str

    @property
    def is_due(self) -> bool:
        return parse_iso(self.next_run_at) <= utc_now()

    def render(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return "\n".join(
            [
                f"# Intake Scheduler Job: {self.name}",
                "",
                f"ID: {self.id}",
                f"Status: {status}",
                f"Type: {self.intake_type}",
                f"Interval: every {self.interval_hours} hour(s)",
                f"Limit: {self.limit_count}",
                f"Send to Telegram: {self.send_to_telegram}",
                f"Feeds path: {self.feeds_path}",
                f"Last run: {self.last_run_at or '-'}",
                f"Next run: {self.next_run_at}",
                "",
                "## Command",
                f"```bash\n{self.command}\n```",
            ]
        ).strip()


class IntakeSchedulerStore:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def create_job(
        self,
        name: str,
        intake_type: str,
        interval_hours: int,
        limit_count: int = 20,
        send_to_telegram: bool = False,
        feeds_path: str = "feeds.yaml",
        enabled: bool = True,
        next_run_at: str | None = None,
    ) -> IntakeSchedulerJob:
        normalized_type = normalize_intake_type(intake_type)
        interval = normalize_interval_hours(interval_hours)
        limit = normalize_limit_count(limit_count)
        now = utc_now_iso()
        next_run = next_run_at or add_hours(now, interval)
        command = build_intake_command(
            intake_type=normalized_type,
            limit_count=limit,
            send_to_telegram=send_to_telegram,
            feeds_path=feeds_path,
        )
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO intake_scheduler_jobs (
                    name, intake_type, command, interval_hours, limit_count, send_to_telegram,
                    feeds_path, enabled, next_run_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name.strip() or default_job_name(normalized_type),
                    normalized_type,
                    command,
                    interval,
                    limit,
                    int(send_to_telegram),
                    feeds_path.strip() or "feeds.yaml",
                    int(enabled),
                    next_run,
                    now,
                    now,
                ),
            )
            job_id = int(cursor.lastrowid)
        job = self.get_job(job_id)
        if job is None:
            raise RuntimeError("Created scheduler job could not be loaded.")
        return job

    def get_job(self, job_id: int) -> IntakeSchedulerJob | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM intake_scheduler_jobs WHERE id = ?", (job_id,)).fetchone()
        return row_to_job(row) if row else None

    def list_jobs(self, include_disabled: bool = True, limit: int = 100) -> list[IntakeSchedulerJob]:
        query = "SELECT * FROM intake_scheduler_jobs"
        params: list[Any] = []
        if not include_disabled:
            query += " WHERE enabled = 1"
        query += " ORDER BY next_run_at ASC, id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [row_to_job(row) for row in rows]

    def due_jobs(self, now: str | None = None, limit: int = 100) -> list[IntakeSchedulerJob]:
        target = now or utc_now_iso()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM intake_scheduler_jobs
                WHERE enabled = 1 AND next_run_at <= ?
                ORDER BY next_run_at ASC, id ASC
                LIMIT ?
                """,
                (target, limit),
            ).fetchall()
        return [row_to_job(row) for row in rows]

    def set_enabled(self, job_id: int, enabled: bool) -> IntakeSchedulerJob:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "UPDATE intake_scheduler_jobs SET enabled = ?, updated_at = ? WHERE id = ?",
                (int(enabled), now, job_id),
            )
        job = self.get_job(job_id)
        if job is None:
            raise ValueError(f"Scheduler job {job_id} does not exist.")
        return job

    def mark_run(self, job_id: int, run_at: str | None = None) -> IntakeSchedulerJob:
        job = self.get_job(job_id)
        if job is None:
            raise ValueError(f"Scheduler job {job_id} does not exist.")
        run_time = run_at or utc_now_iso()
        next_run = add_hours(run_time, job.interval_hours)
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE intake_scheduler_jobs
                SET last_run_at = ?, next_run_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (run_time, next_run, utc_now_iso(), job_id),
            )
        updated = self.get_job(job_id)
        if updated is None:
            raise ValueError(f"Scheduler job {job_id} does not exist.")
        return updated

    def delete_job(self, job_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM intake_scheduler_jobs WHERE id = ?", (job_id,))


def build_intake_command(
    intake_type: str,
    limit_count: int = 20,
    send_to_telegram: bool = False,
    feeds_path: str = "feeds.yaml",
) -> str:
    normalized_type = normalize_intake_type(intake_type)
    limit = normalize_limit_count(limit_count)
    send_flag = " --send" if send_to_telegram else ""
    if normalized_type == "telegram_backfill":
        return f"python -m app.main backfill --limit {limit}{send_flag}"
    if normalized_type == "rss_backfill":
        return f"python -m app.rss_cli backfill --feeds {feeds_path or 'feeds.yaml'} --limit {limit}{send_flag}"
    if normalized_type == "rss_full_article_backfill":
        return f"python -m app.rss_cli backfill --feeds {feeds_path or 'feeds.yaml'} --limit {limit} --fetch-articles{send_flag}"
    raise ValueError(f"Unsupported intake type: {intake_type}")


def scheduler_job_rows(jobs: list[IntakeSchedulerJob]) -> list[dict[str, object]]:
    return [
        {
            "id": job.id,
            "enabled": job.enabled,
            "due": job.is_due,
            "name": job.name,
            "type": job.intake_type,
            "interval_hours": job.interval_hours,
            "limit": job.limit_count,
            "send": job.send_to_telegram,
            "next_run_at": job.next_run_at,
            "last_run_at": job.last_run_at or "-",
            "command": job.command,
        }
        for job in jobs
    ]


def normalize_intake_type(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_INTAKE_JOB_TYPES:
        allowed = ", ".join(sorted(ALLOWED_INTAKE_JOB_TYPES))
        raise ValueError(f"Unsupported intake job type '{value}'. Allowed types: {allowed}")
    return normalized


def normalize_interval_hours(value: int) -> int:
    try:
        hours = int(value)
    except (TypeError, ValueError):
        hours = 1
    return max(1, min(24 * 30, hours))


def normalize_limit_count(value: int) -> int:
    try:
        count = int(value)
    except (TypeError, ValueError):
        count = 20
    return max(1, min(500, count))


def default_job_name(intake_type: str) -> str:
    labels = {
        "telegram_backfill": "Telegram backfill",
        "rss_backfill": "RSS/blog backfill",
        "rss_full_article_backfill": "RSS full-article backfill",
    }
    return labels.get(intake_type, "Intake job")


def row_to_job(row: sqlite3.Row) -> IntakeSchedulerJob:
    return IntakeSchedulerJob(
        id=int(row["id"]),
        name=str(row["name"]),
        intake_type=str(row["intake_type"]),
        command=str(row["command"]),
        interval_hours=int(row["interval_hours"]),
        limit_count=int(row["limit_count"]),
        send_to_telegram=bool(row["send_to_telegram"]),
        feeds_path=str(row["feeds_path"]),
        enabled=bool(row["enabled"]),
        last_run_at=row["last_run_at"],
        next_run_at=str(row["next_run_at"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def add_hours(value: str, hours: int) -> str:
    return (parse_iso(value) + timedelta(hours=normalize_interval_hours(hours))).isoformat()
