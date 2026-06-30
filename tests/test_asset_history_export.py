from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.asset_exporter import export_asset_to_markdown
from app.asset_generator import generate_asset
from app.models import SignalAnalysis, TelegramSignal
from app.storage import SignalStore


def save_test_signal(store: SignalStore) -> int:
    return store.save(
        TelegramSignal(
            source_id="source-1",
            source_title="GitHub Community",
            message_id=1,
            message_text="Useful LangGraph repo for agent memory and evaluation patterns.",
            message_date=datetime.now(timezone.utc),
            permalink="https://t.me/test/1",
        ),
        SignalAnalysis(
            is_valuable=True,
            score=8.5,
            category="AI Engineering",
            summary="A useful repo for agent memory and evaluation patterns.",
            tags=["#agents"],
        ),
        saved_to_telegram=False,
    )


def test_save_asset_history(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_test_signal(store)
    signal = store.get_signal(signal_id)
    assert signal is not None

    asset = generate_asset(signal, "linkedin")
    stored = store.save_asset(asset, rewritten=True)

    assert stored.id > 0
    assert stored.signal_id == signal_id
    assert stored.asset_type == "linkedin"
    assert stored.rewritten is True

    recent = store.recent_assets(limit=5)
    assert [item.id for item in recent] == [stored.id]


def test_export_asset_to_markdown_and_mark_exported(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_test_signal(store)
    signal = store.get_signal(signal_id)
    assert signal is not None

    stored = store.save_asset(generate_asset(signal, "teaching_example"), rewritten=False)
    path = export_asset_to_markdown(stored, tmp_path / "exports")
    store.mark_asset_exported(stored.id, path)
    updated = store.get_asset(stored.id)

    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("---")
    assert updated is not None
    assert updated.exported_path == str(path)


def test_mark_asset_sent(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_test_signal(store)
    signal = store.get_signal(signal_id)
    assert signal is not None

    stored = store.save_asset(generate_asset(signal, "career_note"), rewritten=False)
    store.mark_asset_sent(stored.id)
    updated = store.get_asset(stored.id)

    assert updated is not None
    assert updated.sent_to_telegram is True
    assert updated.sent_at is not None
