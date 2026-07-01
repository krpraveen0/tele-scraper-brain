from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.blueprint_generator import generate_blueprint
from app.idea_lab import generate_idea_lab_report
from app.models import SignalAnalysis, TelegramSignal
from app.storage import SignalStore


def save_signal(store: SignalStore) -> int:
    return store.save(
        TelegramSignal(
            source_id="source-1",
            source_title="Source 1",
            message_id=1,
            message_text="Useful creator signal",
            message_date=datetime.now(timezone.utc),
            permalink="https://t.me/test/1",
        ),
        SignalAnalysis(
            is_valuable=True,
            score=8.0,
            category="AI Engineering",
            summary="Useful creator signal",
            tags=["#agents"],
            suggested_action="Create Medium outline",
        ),
        saved_to_telegram=False,
    )


def test_creator_tables_are_created(tmp_path: Path) -> None:
    db_path = tmp_path / "signals.db"
    SignalStore(db_path)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()

    table_names = {row[0] for row in rows}
    assert {"signals", "ideas", "idea_angles", "blueprints"}.issubset(table_names)


def test_save_idea_report_and_angles(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_signal(store)
    signal = store.get_signal(signal_id)
    assert signal is not None

    report = generate_idea_lab_report(signal)
    idea = store.save_idea_report(report)
    loaded = store.get_idea(idea.id)
    angles = store.idea_angles(idea.id)

    assert loaded == idea
    assert len(angles) == 10
    assert angles[0].idea_id == idea.id
    assert store.recent_ideas(limit=5)[0].id == idea.id


def test_save_blueprint_for_idea(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_signal(store)
    signal = store.get_signal(signal_id)
    assert signal is not None

    report = generate_idea_lab_report(signal)
    idea = store.save_idea_report(report)
    blueprint = generate_blueprint(report, "tech_blog")
    stored = store.save_blueprint(idea.id, blueprint, quality_score=7.5)
    loaded = store.get_blueprint(stored.id)

    assert loaded == stored
    assert stored.idea_id == idea.id
    assert stored.blueprint_type == "tech_blog"
    assert stored.quality_score == 7.5
    assert stored.sections
    assert stored.quality_checklist
    assert "## Structure" in stored.render()
    assert store.recent_blueprints(limit=5)[0].id == stored.id


def test_existing_signal_reads_still_work_after_creator_schema(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_signal(store)

    loaded = store.get_signal(signal_id)
    all_signals = list(store.iter_all())

    assert loaded is not None
    assert loaded.id == signal_id
    assert [signal.id for signal in all_signals] == [signal_id]
