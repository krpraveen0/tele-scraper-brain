from __future__ import annotations

from datetime import datetime, timezone

from app.models import SignalAnalysis, TelegramSignal
from app.sources import SourceConfig, SourceRegistry


def make_signal(source_ref: str | None = "@ai_papers", source_title: str = "AI with Papers") -> TelegramSignal:
    return TelegramSignal(
        source_id="123",
        source_title=source_title,
        message_id=1,
        message_text="A useful paper about agentic AI memory evaluation.",
        message_date=datetime.now(timezone.utc),
        permalink="https://t.me/ai_papers/1",
        source_ref=source_ref,
    )


def test_source_registry_matches_by_handle_and_uses_source_threshold() -> None:
    registry = SourceRegistry(
        [
            SourceConfig(
                name="AI with Papers",
                handle="@ai_papers",
                enabled=True,
                trust_score=9,
                category_hint="Research",
                min_save_score=7.5,
                destination="research",
            )
        ]
    )

    signal = make_signal()

    assert registry.find_for_signal(signal) is not None
    assert registry.min_score_for(signal, default_min_score=7.0) == 7.5


def test_source_registry_routes_source_destination_before_category() -> None:
    registry = SourceRegistry(
        [
            SourceConfig(
                name="AI with Papers",
                handle="@ai_papers",
                destination="research",
            )
        ]
    )
    signal = make_signal()
    analysis = SignalAnalysis(is_valuable=True, score=8.0, category="Career")

    chat = registry.destination_chat_for(
        signal=signal,
        analysis=analysis,
        destinations={"default": "@default", "career": "@career", "research": "@research"},
        default_chat="@default",
    )

    assert chat == "@research"


def test_source_registry_routes_by_category_when_source_destination_is_default() -> None:
    registry = SourceRegistry(
        [
            SourceConfig(
                name="AI with Papers",
                handle="@ai_papers",
                destination="default",
            )
        ]
    )
    signal = make_signal()
    analysis = SignalAnalysis(is_valuable=True, score=8.0, category="Tools")

    chat = registry.destination_chat_for(
        signal=signal,
        analysis=analysis,
        destinations={"default": "@default", "tools": "@tools"},
        default_chat="@default",
    )

    assert chat == "@tools"


def test_legacy_source_registry_uses_source_chats() -> None:
    registry = SourceRegistry.from_legacy_chats(["@one", "@two"], default_min_save_score=7.0)

    assert registry.enabled_chat_refs() == ["@one", "@two"]
    assert registry.min_score_for(make_signal(source_ref="@one", source_title="one"), 5.0) == 7.0
