from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from app.asset_generator import GeneratedAsset
from app.blueprint_generator import Blueprint
from app.dedupe import content_hash
from app.idea_lab import IdeaLabReport
from app.models import (
    FeedbackEntry,
    SignalAnalysis,
    StoredAsset,
    StoredBlueprint,
    StoredIdea,
    StoredIdeaAngle,
    StoredSignal,
    TelegramSignal,
    normalize_feedback_label,
    utc_now_iso,
)


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

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(signal_id) REFERENCES signals(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id INTEGER NOT NULL,
    asset_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    rewritten INTEGER NOT NULL DEFAULT 0,
    exported_path TEXT NOT NULL DEFAULT '',
    sent_to_telegram INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    sent_at TEXT,
    FOREIGN KEY(signal_id) REFERENCES signals(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id INTEGER NOT NULL,
    core_insight TEXT NOT NULL,
    hidden_gap TEXT NOT NULL,
    novel_angle TEXT NOT NULL,
    recommended_format TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(signal_id) REFERENCES signals(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS idea_angles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER NOT NULL,
    angle_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    target_audience TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    FOREIGN KEY(idea_id) REFERENCES ideas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blueprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER NOT NULL,
    blueprint_type TEXT NOT NULL,
    title TEXT NOT NULL,
    audience TEXT NOT NULL,
    promise TEXT NOT NULL,
    opening_scene TEXT NOT NULL,
    unique_angle TEXT NOT NULL,
    framework TEXT NOT NULL,
    sections_json TEXT NOT NULL,
    diagram_idea TEXT NOT NULL,
    conclusion TEXT NOT NULL,
    call_to_action TEXT NOT NULL,
    quality_checklist_json TEXT NOT NULL,
    quality_score REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(idea_id) REFERENCES ideas(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at);
CREATE INDEX IF NOT EXISTS idx_signals_category_score ON signals(category, score);
CREATE INDEX IF NOT EXISTS idx_signals_saved ON signals(saved_to_telegram);
CREATE INDEX IF NOT EXISTS idx_feedback_signal_id ON feedback(signal_id);
CREATE INDEX IF NOT EXISTS idx_feedback_label ON feedback(label);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_assets_signal_id ON assets(signal_id);
CREATE INDEX IF NOT EXISTS idx_assets_type_created_at ON assets(asset_type, created_at);
CREATE INDEX IF NOT EXISTS idx_assets_sent ON assets(sent_to_telegram);
CREATE INDEX IF NOT EXISTS idx_ideas_signal_id ON ideas(signal_id);
CREATE INDEX IF NOT EXISTS idx_ideas_created_at ON ideas(created_at);
CREATE INDEX IF NOT EXISTS idx_idea_angles_idea_id ON idea_angles(idea_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_idea_id ON blueprints(idea_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_type_created_at ON blueprints(blueprint_type, created_at);
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
        text_hash = content_hash(signal.message_text)
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
                    text_hash,
                    int(analysis.is_valuable),
                    analysis.score,
                    analysis.category,
                    analysis.reason,
                    analysis.summary,
                    json.dumps(analysis.tags),
                    analysis.suggested_action,
                    analysis.to_json(),
                    int(saved_to_telegram),
                    utc_now_iso(),
                ),
            )
            if cursor.lastrowid:
                return int(cursor.lastrowid)

            existing = conn.execute(
                """
                SELECT id FROM signals
                WHERE (source_id = ? AND message_id = ?) OR content_hash = ?
                LIMIT 1
                """,
                (signal.source_id, signal.message_id, text_hash),
            ).fetchone()
            return int(existing["id"]) if existing else 0

    def get_signal(self, signal_id: int) -> StoredSignal | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
        return self._row_to_signal(row) if row else None

    def mark_saved_to_telegram(self, signal_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE signals SET saved_to_telegram = 1 WHERE id = ?",
                (signal_id,),
            )

    def save_asset(self, asset: GeneratedAsset, rewritten: bool = False) -> StoredAsset:
        created_at = utc_now_iso()
        with self._connect() as conn:
            signal = conn.execute("SELECT 1 FROM signals WHERE id = ?", (asset.signal_id,)).fetchone()
            if signal is None:
                raise ValueError(f"Signal id {asset.signal_id} does not exist.")
            cursor = conn.execute(
                """
                INSERT INTO assets (signal_id, asset_type, title, body, rewritten, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (asset.signal_id, asset.asset_type, asset.title, asset.body, int(rewritten), created_at),
            )
            asset_id = int(cursor.lastrowid)
        return StoredAsset(
            id=asset_id,
            signal_id=asset.signal_id,
            asset_type=asset.asset_type,
            title=asset.title,
            body=asset.body,
            rewritten=rewritten,
            exported_path="",
            sent_to_telegram=False,
            created_at=created_at,
            sent_at=None,
        )

    def get_asset(self, asset_id: int) -> StoredAsset | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        return self._row_to_asset(row) if row else None

    def recent_assets(self, limit: int = 20) -> list[StoredAsset]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM assets
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_asset(row) for row in rows]

    def mark_asset_exported(self, asset_id: int, exported_path: Path | str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE assets SET exported_path = ? WHERE id = ?",
                (str(exported_path), asset_id),
            )

    def mark_asset_sent(self, asset_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE assets SET sent_to_telegram = 1, sent_at = ? WHERE id = ?",
                (utc_now_iso(), asset_id),
            )

    def save_idea_report(self, report: IdeaLabReport) -> StoredIdea:
        created_at = utc_now_iso()
        with self._connect() as conn:
            signal = conn.execute("SELECT 1 FROM signals WHERE id = ?", (report.signal_id,)).fetchone()
            if signal is None:
                raise ValueError(f"Signal id {report.signal_id} does not exist.")
            cursor = conn.execute(
                """
                INSERT INTO ideas (signal_id, core_insight, hidden_gap, novel_angle, recommended_format, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (report.signal_id, report.core_insight, report.hidden_gap, report.novel_angle, report.recommended_format, created_at),
            )
            idea_id = int(cursor.lastrowid)
            conn.executemany(
                """
                INSERT INTO idea_angles (idea_id, angle_type, title, description, target_audience, score)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (idea_id, angle.angle_type, angle.title, angle.description, angle.target_audience, 0.0)
                    for angle in report.content_angles
                ],
            )
        return StoredIdea(
            id=idea_id,
            signal_id=report.signal_id,
            core_insight=report.core_insight,
            hidden_gap=report.hidden_gap,
            novel_angle=report.novel_angle,
            recommended_format=report.recommended_format,
            created_at=created_at,
        )

    def get_idea(self, idea_id: int) -> StoredIdea | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()
        return self._row_to_idea(row) if row else None

    def recent_ideas(self, limit: int = 20) -> list[StoredIdea]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM ideas
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_idea(row) for row in rows]

    def idea_angles(self, idea_id: int) -> list[StoredIdeaAngle]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM idea_angles
                WHERE idea_id = ?
                ORDER BY id ASC
                """,
                (idea_id,),
            ).fetchall()
        return [self._row_to_idea_angle(row) for row in rows]

    def save_blueprint(self, idea_id: int, blueprint: Blueprint, quality_score: float = 0.0) -> StoredBlueprint:
        created_at = utc_now_iso()
        sections = [
            {"title": section.title, "purpose": section.purpose, "bullets": section.bullets}
            for section in blueprint.sections
        ]
        with self._connect() as conn:
            idea = conn.execute("SELECT 1 FROM ideas WHERE id = ?", (idea_id,)).fetchone()
            if idea is None:
                raise ValueError(f"Idea id {idea_id} does not exist.")
            cursor = conn.execute(
                """
                INSERT INTO blueprints (
                    idea_id,
                    blueprint_type,
                    title,
                    audience,
                    promise,
                    opening_scene,
                    unique_angle,
                    framework,
                    sections_json,
                    diagram_idea,
                    conclusion,
                    call_to_action,
                    quality_checklist_json,
                    quality_score,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idea_id,
                    blueprint.blueprint_type,
                    blueprint.title,
                    blueprint.audience,
                    blueprint.promise,
                    blueprint.opening_scene,
                    blueprint.unique_angle,
                    blueprint.framework,
                    json.dumps(sections, ensure_ascii=False),
                    blueprint.diagram_idea,
                    blueprint.conclusion,
                    blueprint.call_to_action,
                    json.dumps(blueprint.quality_checklist, ensure_ascii=False),
                    quality_score,
                    created_at,
                ),
            )
            blueprint_id = int(cursor.lastrowid)
        return StoredBlueprint(
            id=blueprint_id,
            idea_id=idea_id,
            blueprint_type=blueprint.blueprint_type,
            title=blueprint.title,
            audience=blueprint.audience,
            promise=blueprint.promise,
            opening_scene=blueprint.opening_scene,
            unique_angle=blueprint.unique_angle,
            framework=blueprint.framework,
            sections=sections,
            diagram_idea=blueprint.diagram_idea,
            conclusion=blueprint.conclusion,
            call_to_action=blueprint.call_to_action,
            quality_checklist=blueprint.quality_checklist,
            quality_score=quality_score,
            created_at=created_at,
        )

    def get_blueprint(self, blueprint_id: int) -> StoredBlueprint | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM blueprints WHERE id = ?", (blueprint_id,)).fetchone()
        return self._row_to_blueprint(row) if row else None

    def recent_blueprints(self, limit: int = 20) -> list[StoredBlueprint]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM blueprints
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_blueprint(row) for row in rows]

    def add_feedback(self, signal_id: int, label: str, notes: str = "") -> FeedbackEntry:
        normalized_label = normalize_feedback_label(label)
        created_at = utc_now_iso()
        with self._connect() as conn:
            signal = conn.execute("SELECT 1 FROM signals WHERE id = ?", (signal_id,)).fetchone()
            if signal is None:
                raise ValueError(f"Signal id {signal_id} does not exist.")
            cursor = conn.execute(
                """
                INSERT INTO feedback (signal_id, label, notes, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (signal_id, normalized_label, notes.strip(), created_at),
            )
            feedback_id = int(cursor.lastrowid)
        return FeedbackEntry(id=feedback_id, signal_id=signal_id, label=normalized_label, notes=notes.strip(), created_at=created_at)

    def feedback_for_signal(self, signal_id: int) -> list[FeedbackEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM feedback
                WHERE signal_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (signal_id,),
            ).fetchall()
        return [self._row_to_feedback(row) for row in rows]

    def recent_feedback(self, limit: int = 20) -> list[FeedbackEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM feedback
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_feedback(row) for row in rows]

    def feedback_summary(self) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    f.label,
                    COUNT(*) AS count,
                    AVG(s.score) AS avg_score,
                    SUM(CASE WHEN s.saved_to_telegram = 1 THEN 1 ELSE 0 END) AS sent
                FROM feedback f
                JOIN signals s ON s.id = f.signal_id
                GROUP BY f.label
                ORDER BY count DESC, f.label ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

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

    def unsent_saved(self, limit: int = 20) -> list[StoredSignal]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM signals
                WHERE is_valuable = 1 AND saved_to_telegram = 0
                ORDER BY score DESC, created_at DESC
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

    def source_stats(self) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    source_title,
                    COUNT(*) AS total,
                    SUM(CASE WHEN is_valuable = 1 THEN 1 ELSE 0 END) AS valuable,
                    SUM(CASE WHEN saved_to_telegram = 1 THEN 1 ELSE 0 END) AS sent,
                    AVG(score) AS avg_score,
                    MAX(score) AS max_score
                FROM signals
                GROUP BY source_title
                ORDER BY valuable DESC, avg_score DESC, total DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

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
            analysis=SignalAnalysis.from_json(row["analysis_json"]),
            saved_to_telegram=bool(row["saved_to_telegram"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_feedback(row: sqlite3.Row) -> FeedbackEntry:
        return FeedbackEntry(
            id=int(row["id"]),
            signal_id=int(row["signal_id"]),
            label=row["label"],
            notes=row["notes"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_asset(row: sqlite3.Row) -> StoredAsset:
        return StoredAsset(
            id=int(row["id"]),
            signal_id=int(row["signal_id"]),
            asset_type=row["asset_type"],
            title=row["title"],
            body=row["body"],
            rewritten=bool(row["rewritten"]),
            exported_path=row["exported_path"],
            sent_to_telegram=bool(row["sent_to_telegram"]),
            created_at=row["created_at"],
            sent_at=row["sent_at"],
        )

    @staticmethod
    def _row_to_idea(row: sqlite3.Row) -> StoredIdea:
        return StoredIdea(
            id=int(row["id"]),
            signal_id=int(row["signal_id"]),
            core_insight=row["core_insight"],
            hidden_gap=row["hidden_gap"],
            novel_angle=row["novel_angle"],
            recommended_format=row["recommended_format"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_idea_angle(row: sqlite3.Row) -> StoredIdeaAngle:
        return StoredIdeaAngle(
            id=int(row["id"]),
            idea_id=int(row["idea_id"]),
            angle_type=row["angle_type"],
            title=row["title"],
            description=row["description"],
            target_audience=row["target_audience"],
            score=float(row["score"] or 0.0),
        )

    @staticmethod
    def _row_to_blueprint(row: sqlite3.Row) -> StoredBlueprint:
        return StoredBlueprint(
            id=int(row["id"]),
            idea_id=int(row["idea_id"]),
            blueprint_type=row["blueprint_type"],
            title=row["title"],
            audience=row["audience"],
            promise=row["promise"],
            opening_scene=row["opening_scene"],
            unique_angle=row["unique_angle"],
            framework=row["framework"],
            sections=json.loads(row["sections_json"]),
            diagram_idea=row["diagram_idea"],
            conclusion=row["conclusion"],
            call_to_action=row["call_to_action"],
            quality_checklist=json.loads(row["quality_checklist_json"]),
            quality_score=float(row["quality_score"] or 0.0),
            created_at=row["created_at"],
        )
