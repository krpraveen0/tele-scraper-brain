from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.asset_generator import generate_asset
from app.daily_action_brief import build_daily_action_brief
from app.models import SignalAnalysis, TelegramSignal
from app.storage import SignalStore


def save_signal(store: SignalStore, message_id: int, category: str, score: float, summary: str) -> int:
    return store.save(
        TelegramSignal(
            source_id=f"source-{message_id}",
            source_title=f"Source {message_id}",
            message_id=message_id,
            message_text=f"Useful {category} signal {message_id}",
            message_date=datetime.now(timezone.utc),
            permalink=f"https://t.me/test/{message_id}",
        ),
        SignalAnalysis(
            is_valuable=True,
            score=score,
            category=category,
            reason=f"Reason for {category}",
            summary=summary,
            tags=["#test"],
            suggested_action="Read today",
        ),
        saved_to_telegram=False,
    )


def test_daily_action_brief_includes_goal_slots(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    save_signal(store, 1, "Career", 9.0, "Remote AI role with RAG and LangGraph.")
    save_signal(store, 2, "AI Engineering", 8.5, "Agent memory evaluation pattern.")
    save_signal(store, 3, "Teaching", 8.0, "Python collections classroom idea.")
    save_signal(store, 4, "Global Economy", 7.5, "AI infra spending signal.")

    brief = build_daily_action_brief(store, hours=24, limit=20)

    assert "# Daily Action Brief" in brief
    assert "Career move" in brief
    assert "AI engineering learning" in brief
    assert "Teaching idea" in brief
    assert "Economy awareness" in brief
    assert "Remote AI role" in brief
    assert "Agent memory" in brief


def test_daily_action_brief_empty_window_has_recovery_flow(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")

    brief = build_daily_action_brief(store, hours=24, limit=20)

    assert "No high-value saved signals" in brief
    assert "python -m app.main backfill --limit 20" in brief
    assert "Feedback snapshot" in brief


def test_daily_action_brief_includes_assets_and_feedback(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_signal(store, 1, "Content", 8.0, "LinkedIn post idea about Signal OS.")
    signal = store.get_signal(signal_id)
    assert signal is not None
    asset = store.save_asset(generate_asset(signal, "linkedin"), rewritten=False)
    store.mark_asset_sent(asset.id)
    store.add_feedback(signal_id, "linkedin_idea")

    brief = build_daily_action_brief(store, hours=24, limit=20)

    assert "Asset follow-up" in brief
    assert f"Asset {asset.id}" in brief
    assert "linkedin_idea" in brief
    assert "Content idea" in brief


def test_daily_action_brief_does_not_reuse_same_signal_for_all_slots(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    first_id = save_signal(store, 1, "Career", 9.0, "Career signal.")
    second_id = save_signal(store, 2, "Career", 8.0, "Second career signal.")

    brief = build_daily_action_brief(store, hours=24, limit=20)

    assert f"Signal ID: {first_id}" in brief
    assert f"Signal ID: {second_id}" in brief
