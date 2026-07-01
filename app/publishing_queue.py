from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path

from app.models import utc_now_iso

QUEUE_STATUSES = (
    "idea_captured",
    "blueprint_generated",
    "draft_started",
    "needs_diagram",
    "needs_references",
    "ready_to_polish",
    "ready_to_publish",
    "published",
    "repurpose_later",
)

QUEUE_PLATFORMS = (
    "linkedin",
    "medium",
    "course",
    "podcast",
    "storybook",
)

QUEUE_CONTENT_TYPES = (
    "idea",
    "blueprint",
    "draft",
    "linkedin_post",
    "medium_article",
    "course_module",
    "podcast_script",
    "storybook_chapter",
    "series",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS publishing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_signal_id INTEGER,
    idea_id INTEGER,
    blueprint_id INTEGER,
    title TEXT NOT NULL,
    content_type TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 3,
    notes TEXT NOT NULL DEFAULT '',
    published_url TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_publishing_queue_status ON publishing_queue(status);
CREATE INDEX IF NOT EXISTS idx_publishing_queue_platform ON publishing_queue(platform);
CREATE INDEX IF NOT EXISTS idx_publishing_queue_priority ON publishing_queue(priority);
CREATE INDEX IF NOT EXISTS idx_publishing_queue_updated_at ON publishing_queue(updated_at);
"""


@dataclass(frozen=True)
class QueueItem:
    id: int
    source_signal_id: int | None
    idea_id: int | None
    blueprint_id: int | None
    title: str
    content_type: str
    platform: str
    status: str
    priority: int
    notes: str
    published_url: str
    created_at: str
    updated_at: str

    def render(self) -> str:
        return "\n".join(
            [
                f"# {self.title}",
                "",
                f"Status: {self.status}",
                f"Platform: {self.platform}",
                f"Content type: {self.content_type}",
                f"Priority: {self.priority}",
                f"Published URL: {self.published_url or '-'}",
                "",
                self.notes,
            ]
        ).strip()


class PublishingQueue:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def add_item(
        self,
        title: str,
        platform: str,
        content_type: str,
        status: str = "idea_captured",
        priority: int = 3,
        source_signal_id: int | None = None,
        idea_id: int | None = None,
        blueprint_id: int | None = None,
        notes: str = "",
    ) -> QueueItem:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Queue item title is required.")

        normalized_platform = normalize_platform(platform)
        normalized_type = normalize_content_type(content_type)
        normalized_status = normalize_status(status)
        clean_priority = normalize_priority(priority)
        now = utc_now_iso()

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO publishing_queue (
                    source_signal_id,
                    idea_id,
                    blueprint_id,
                    title,
                    content_type,
                    platform,
                    status,
                    priority,
                    notes,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_signal_id,
                    idea_id,
                    blueprint_id,
                    clean_title,
                    normalized_type,
                    normalized_platform,
                    normalized_status,
                    clean_priority,
                    notes.strip(),
                    now,
                    now,
                ),
            )
            item_id = int(cursor.lastrowid)

        return QueueItem(
            id=item_id,
            source_signal_id=source_signal_id,
            idea_id=idea_id,
            blueprint_id=blueprint_id,
            title=clean_title,
            content_type=normalized_type,
            platform=normalized_platform,
            status=normalized_status,
            priority=clean_priority,
            notes=notes.strip(),
            published_url="",
            created_at=now,
            updated_at=now,
        )

    def get_item(self, item_id: int) -> QueueItem | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM publishing_queue WHERE id = ?", (item_id,)).fetchone()
        return row_to_queue_item(row) if row else None

    def list_items(self, status: str | None = None, platform: str | None = None, limit: int = 100) -> list[QueueItem]:
        clauses: list[str] = []
        params: list[object] = []
        if status and status != "all":
            clauses.append("status = ?")
            params.append(normalize_status(status))
        if platform and platform != "all":
            clauses.append("platform = ?")
            params.append(normalize_platform(platform))

        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        query = f"""
            SELECT * FROM publishing_queue
            {where}
            ORDER BY priority ASC, updated_at DESC, id DESC
            LIMIT ?
        """
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [row_to_queue_item(row) for row in rows]

    def update_status(self, item_id: int, status: str, published_url: str | None = None) -> QueueItem:
        normalized_status = normalize_status(status)
        now = utc_now_iso()
        with self._connect() as conn:
            existing = conn.execute("SELECT 1 FROM publishing_queue WHERE id = ?", (item_id,)).fetchone()
            if existing is None:
                raise ValueError(f"Queue item id {item_id} does not exist.")
            if published_url is None:
                conn.execute(
                    "UPDATE publishing_queue SET status = ?, updated_at = ? WHERE id = ?",
                    (normalized_status, now, item_id),
                )
            else:
                conn.execute(
                    "UPDATE publishing_queue SET status = ?, published_url = ?, updated_at = ? WHERE id = ?",
                    (normalized_status, published_url.strip(), now, item_id),
                )
        item = self.get_item(item_id)
        if item is None:
            raise ValueError(f"Queue item id {item_id} does not exist.")
        return item


def normalize_status(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in QUEUE_STATUSES:
        allowed = ", ".join(QUEUE_STATUSES)
        raise ValueError(f"Unsupported queue status '{value}'. Allowed statuses: {allowed}")
    return normalized


def normalize_platform(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in QUEUE_PLATFORMS:
        allowed = ", ".join(QUEUE_PLATFORMS)
        raise ValueError(f"Unsupported queue platform '{value}'. Allowed platforms: {allowed}")
    return normalized


def normalize_content_type(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in QUEUE_CONTENT_TYPES:
        allowed = ", ".join(QUEUE_CONTENT_TYPES)
        raise ValueError(f"Unsupported content type '{value}'. Allowed types: {allowed}")
    return normalized


def normalize_priority(value: int) -> int:
    number = int(value)
    if number < 1 or number > 5:
        raise ValueError("Priority must be between 1 and 5.")
    return number


def row_to_queue_item(row: sqlite3.Row) -> QueueItem:
    return QueueItem(
        id=int(row["id"]),
        source_signal_id=row["source_signal_id"],
        idea_id=row["idea_id"],
        blueprint_id=row["blueprint_id"],
        title=row["title"],
        content_type=row["content_type"],
        platform=row["platform"],
        status=row["status"],
        priority=int(row["priority"]),
        notes=row["notes"],
        published_url=row["published_url"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
