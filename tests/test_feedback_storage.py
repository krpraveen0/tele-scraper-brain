from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models import SignalAnalysis, TelegramSignal
from app.storage import SignalStore


def make_signal(message_id: int = 1) -> TelegramSignal:
    return TelegramSignal(
        source_id="source-1",
        source_title="Test Source",
        message_id=message_id,
        message_text=f"Remote AI Engineer role #{message_id} with Python, RAG, LangGraph and tracing.",
        message_date=datetime.now(timezone.utc),
        permalink=f"https://t.me/test/{message_id}",
    )


def test_add_feedback_to_existing_signal(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = store.save(
        make_signal(),
        SignalAnalysis(is_valuable=True, score=8.5, category="Career"),
        saved_to_telegram=False,
    )

    feedback = store.add_feedback(signal_id=signal_id, label="linkedin-idea", notes="Good post idea")

    assert feedback.signal_id == signal_id
    assert feedback.label == "linkedin_idea"
    assert feedback.notes == "Good post idea"
    assert len(store.feedback_for_signal(signal_id)) == 1


def test_add_feedback_rejects_missing_signal(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")

    with pytest.raises(ValueError, match="does not exist"):
        store.add_feedback(signal_id=999, label="useful")


def test_add_feedback_rejects_unknown_label(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = store.save(
        make_signal(),
        SignalAnalysis(is_valuable=True, score=8.5, category="Career"),
        saved_to_telegram=False,
    )

    with pytest.raises(ValueError, match="Unsupported feedback label"):
        store.add_feedback(signal_id=signal_id, label="random")


def test_feedback_summary_counts_labels(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    first_id = store.save(
        make_signal(message_id=1),
        SignalAnalysis(is_valuable=True, score=8.5, category="Career"),
        saved_to_telegram=True,
    )
    second_id = store.save(
        make_signal(message_id=2),
        SignalAnalysis(is_valuable=True, score=7.5, category="Tools"),
        saved_to_telegram=False,
    )

    assert first_id != second_id

    store.add_feedback(signal_id=first_id, label="useful")
    store.add_feedback(signal_id=second_id, label="useful")
    store.add_feedback(signal_id=second_id, label="tool_to_try")

    summary = {row["label"]: row for row in store.feedback_summary()}

    assert summary["useful"]["count"] == 2
    assert summary["useful"]["sent"] == 1
    assert summary["tool_to_try"]["count"] == 1


def test_recent_feedback_orders_latest_first(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = store.save(
        make_signal(),
        SignalAnalysis(is_valuable=True, score=8.5, category="Career"),
        saved_to_telegram=False,
    )

    first = store.add_feedback(signal_id=signal_id, label="useful")
    second = store.add_feedback(signal_id=signal_id, label="read_weekend")

    recent = store.recent_feedback(limit=2)

    assert [entry.id for entry in recent] == [second.id, first.id]
