from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.asset_generator import generate_asset
from app.feedback_profile import build_feedback_profile
from app.models import SignalAnalysis, TelegramSignal
from app.storage import SignalStore


def save_signal(
    store: SignalStore,
    message_id: int,
    source_title: str,
    category: str,
    summary: str,
    tags: list[str],
) -> int:
    return store.save(
        TelegramSignal(
            source_id=f"source-{message_id}",
            source_title=source_title,
            message_id=message_id,
            message_text=f"Useful signal {message_id}: {summary}",
            message_date=datetime.now(timezone.utc),
            permalink=f"https://t.me/test/{message_id}",
        ),
        SignalAnalysis(
            is_valuable=True,
            score=8.0,
            category=category,
            reason=f"Reason for {category}",
            summary=summary,
            tags=tags,
            suggested_action="Read today",
        ),
        saved_to_telegram=False,
    )


def test_feedback_profile_empty_state(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")

    profile = build_feedback_profile(store)

    assert "No feedback-labelled signals found yet" in profile
    assert "python -m app.main feedback --id <signal_id> --label useful" in profile


def test_feedback_profile_detects_liked_and_ignored_patterns(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    career_id = save_signal(store, 1, "Career Source", "Career", "Remote AI role with RAG.", ["#career", "#rag"])
    noisy_id = save_signal(store, 2, "Noisy Source", "Content", "Generic motivational AI post.", ["#hype"])

    store.add_feedback(career_id, "career_opportunity")
    store.add_feedback(career_id, "useful")
    store.add_feedback(noisy_id, "not_useful", notes="Too generic")

    profile = build_feedback_profile(store)

    assert "What Praveen likes" in profile
    assert "Career" in profile
    assert "career_opportunity" in profile
    assert "What Praveen ignores" in profile
    assert "Noisy Source" in profile
    assert "#rag" in profile
    assert "#hype" in profile


def test_feedback_profile_includes_asset_outcomes(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_signal(store, 1, "AI Source", "AI Engineering", "Agent memory pattern.", ["#agents"])
    signal = store.get_signal(signal_id)
    assert signal is not None

    asset = store.save_asset(generate_asset(signal, "linkedin"), rewritten=True)
    store.mark_asset_sent(asset.id)
    store.add_feedback(signal_id, "linkedin_idea")

    profile = build_feedback_profile(store)

    assert "Asset outcomes" in profile
    assert "linkedin" in profile
    assert "Sent to Telegram: 1" in profile
    assert "Assets connected to labelled signals: 1" in profile


def test_feedback_profile_produces_tuning_suggestions(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    good_id = save_signal(store, 1, "Research Source", "Research", "Useful paper on evals.", ["#evals"])
    bad_id = save_signal(store, 2, "Content Source", "Content", "Generic AI news.", ["#news"])

    store.add_feedback(good_id, "research_note")
    store.add_feedback(bad_id, "archive")

    profile = build_feedback_profile(store)

    assert "Prompt and source tuning suggestions" in profile
    assert "Boost signals in Research" in profile
    assert "Penalize generic Content" in profile
