from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from app.dedupe import content_hash
from app.models import SignalAnalysis, StoredSignal, TelegramSignal, utc_now_iso


SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    source_title TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    message_date TEXT NOT NULL,
    permalink TEXT,
    content_hash TEXT NOT NULL,
    is_valuable INTEGER NOT NULL,
    score REAL NOT NULL,
    category TEXT NOT NULL,
    reason TEXT NOT NULL,
    summary TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    suggested_action TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    saved_to_telegram INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    UNIQUE(source_id, message_id),
    UNIQUE(content_hash)
);

CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at);
CREATE INDEX IF NOT EXISTS idx_signals_category_score ON signals(category, score);
CREATE INDEX IF NOT EXISTS idx_signals_saved ON signals(saved_to_telegram);
"""


class SignalStore:
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

    def exists(self, signal: TelegramSignal) -> bool:
        text_hash = content_hash(signal.message_text)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1 FROM signals
                WHERE (source_id = ? AND message_id = ?) OR content_hash = ?
                LIMIT 1
                """,
                (signal.source_id, signal.message_id, text_hash),
            ).fetchone()
        return row is not None

    def save(self, signal: TelegramSignal, analysis: SignalAnalysis, saved_to_telegram: bool) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO signals (
                    source_id,
                    source_title,
                    message_id,
                    message_text,
                    message_date,
                    permalink,
                    content_hash,
                    is_valuable,
                    score,
                    category,
                    reason,
                    summary,
                    tags_json,
                    suggested_action,
                    analysis_json,
                    saved_to_telegram,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.source_id,
                    signal.source_title,
                    signal.message_id,
                    signal.message_text,
                    signal.message_date.isoformat(timespec="seconds"),
                    signal.permalink,
                    content_hash(signal.message_text),
                    int(analysis.is_valuable),
                    analysis.score,
                    analysis.category,
                    analysis.reason,
                    analysis.summary,
                    json.dumps(analysis.tags),
                    analysis.suggested_action,
                    analysis.model_dump_json(),
                    int(saved_to_telegram),
                    utc_now_iso(),
                ),
            )
            return int(cursor.lastrowid or 0)

    def mark_saved_to_telegram(self, signal_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE signals SET saved_to_telegram = 1 WHERE id = ?",
                (signal_id,),
            )

    def recent_saved(self, limit: int = 20) -> list[StoredSignal]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM signals
                WHERE is_valuable = 1 AND saved_to_telegram = 1
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_signal(row) for row in rows]

    def saved_since(self, iso_datetime: str, limit: int = 50) -> list[StoredSignal]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM signals
                WHERE is_valuable = 1 AND created_at >= ?
                ORDER BY score DESC, created_at DESC
                LIMIT ?
                """,
                (iso_datetime, limit),
            ).fetchall()
        return [self._row_to_signal(row) for row in rows]

    def iter_all(self) -> Iterable[StoredSignal]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM signals ORDER BY created_at DESC").fetchall()
        for row in rows:
            yield self._row_to_signal(row)

    @staticmethod
    def _row_to_signal(row: sqlite3.Row) -> StoredSignal:
        return StoredSignal(
            id=int(row["id"]),
            source_id=row["source_id"],
            source_title=row["source_title"],
            message_id=int(row["message_id"]),
            message_text=row["message_text"],
            message_date=row["message_date"],
            permalink=row["permalink"],
            analysis=SignalAnalysis.model_validate_json(row["analysis_json"]),
            saved_to_telegram=bool(row["saved_to_telegram"]),
            created_at=row["created_at"],
        )
