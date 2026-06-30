from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.models import SignalAnalysis, TelegramSignal
from app.storage import SignalStore


def test_get_signal_returns_saved_signal_by_id(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = store.save(
        TelegramSignal(
            source_id="source-1",
            source_title="Test Source",
            message_id=1,
            message_text="Useful AI engineering signal for asset generation.",
            message_date=datetime.now(timezone.utc),
            permalink="https://t.me/test/1",
        ),
        SignalAnalysis(is_valuable=True, score=8.0, category="AI Engineering", summary="Useful summary"),
        saved_to_telegram=False,
    )

    signal = store.get_signal(signal_id)

    assert signal is not None
    assert signal.id == signal_id
    assert signal.source_title == "Test Source"
    assert signal.analysis.summary == "Useful summary"


def test_get_signal_returns_none_for_missing_id(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")

    assert store.get_signal(999) is None
