from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.creator_services import allowed_blueprint_types, create_blueprint
from app.models import SignalAnalysis, TelegramSignal
from app.storage import SignalStore


def save_signal(store: SignalStore) -> int:
    return store.save(
        TelegramSignal(
            source_id="source-1",
            source_title="Source 1",
            message_id=1,
            message_text="Useful AI engineering signal",
            message_date=datetime.now(timezone.utc),
            permalink="https://t.me/test/1",
        ),
        SignalAnalysis(
            is_valuable=True,
            score=8.0,
            category="AI Engineering",
            summary="Useful AI engineering signal",
            tags=["#agents"],
            suggested_action="Create Medium outline",
        ),
        saved_to_telegram=False,
    )


def test_create_blueprint_from_store(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_signal(store)

    blueprint = create_blueprint(store, signal_id, "tech_blog")

    assert blueprint.signal_id == signal_id
    assert blueprint.blueprint_type == "tech_blog"
    assert "## Structure" in blueprint.render()


def test_allowed_blueprint_types_are_exposed() -> None:
    assert "tech_blog" in allowed_blueprint_types()
    assert "course_module" in allowed_blueprint_types()
