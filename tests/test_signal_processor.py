from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from rich.console import Console

from app.models import SignalAnalysis, TelegramSignal
from app.signal_processor import SignalProcessor
from app.sources import SourceConfig, SourceRegistry
from app.storage import SignalStore


class StubAnalyzer:
    def __init__(self, analysis: SignalAnalysis) -> None:
        self.analysis = analysis
        self.calls = 0

    def analyze(self, message_text: str) -> SignalAnalysis:
        self.calls += 1
        return self.analysis


class ProcessorSettings(SimpleNamespace):
    def min_save_score_for(self, signal: TelegramSignal) -> float:
        return self.source_registry.min_score_for(signal, self.min_save_score)

    def destination_for(self, signal: TelegramSignal, analysis: SignalAnalysis) -> str:
        return self.source_registry.destination_chat_for(signal, analysis, {"default": "@default"}, "@default")


@pytest.fixture
def settings(tmp_path: Path):
    return ProcessorSettings(
        llm_provider="test",
        min_save_score=7.0,
        max_message_chars=5000,
        database_path=tmp_path / "signals.db",
        source_registry=SourceRegistry.empty(),
    )


@pytest.fixture
def quiet_console() -> Console:
    return Console(file=StringIO(), force_terminal=False, width=120)


def make_signal(text: str, message_id: int = 1, source_ref: str | None = None) -> TelegramSignal:
    return TelegramSignal(
        source_id="source-1",
        source_title="Test Source",
        message_id=message_id,
        message_text=text,
        message_date=datetime.now(timezone.utc),
        permalink="https://t.me/test/1",
        source_ref=source_ref,
    )


@pytest.mark.asyncio
async def test_process_saves_high_value_signal_locally(settings, quiet_console) -> None:
    store = SignalStore(settings.database_path)
    analyzer = StubAnalyzer(
        SignalAnalysis(
            is_valuable=True,
            score=8.5,
            category="Career",
            reason="Strong remote AI role match.",
            summary="Remote AI role requiring Python and LangGraph.",
            tags=["#career"],
            suggested_action="Apply",
        )
    )
    processor = SignalProcessor(settings, store, analyzer, console=quiet_console)

    result = await processor.process(make_signal("Remote AI Engineer role with Python, RAG, LangGraph and tracing."))

    assert result.status == "saved_local"
    assert result.analysis is not None
    assert result.analysis.score == 8.5
    assert analyzer.calls == 1
    assert len(list(store.iter_all())) == 1
    assert len(store.unsent_saved()) == 1
    assert len(store.recent_saved()) == 0


@pytest.mark.asyncio
async def test_source_specific_threshold_can_reject_signal(settings, quiet_console) -> None:
    settings.source_registry = SourceRegistry(
        [
            SourceConfig(
                name="Strict Source",
                handle="@strict_source",
                min_save_score=9.0,
            )
        ]
    )
    store = SignalStore(settings.database_path)
    analyzer = StubAnalyzer(SignalAnalysis(is_valuable=True, score=8.5, category="Career"))
    processor = SignalProcessor(settings, store, analyzer, console=quiet_console)

    result = await processor.process(
        make_signal("Remote AI Engineer role with Python, RAG, LangGraph and tracing.", source_ref="@strict_source")
    )

    assert result.status == "ignored"
    assert analyzer.calls == 1
    assert len(store.unsent_saved()) == 0


@pytest.mark.asyncio
async def test_process_skips_duplicate_without_llm_call(settings, quiet_console) -> None:
    store = SignalStore(settings.database_path)
    analyzer = StubAnalyzer(SignalAnalysis(is_valuable=True, score=9.0, category="Career"))
    processor = SignalProcessor(settings, store, analyzer, console=quiet_console)
    signal = make_signal("Remote AI Engineer role with Python, RAG, LangGraph and tracing.")

    first = await processor.process(signal)
    second = await processor.process(signal)

    assert first.status == "saved_local"
    assert second.status == "duplicate"
    assert analyzer.calls == 1
    assert len(list(store.iter_all())) == 1


@pytest.mark.asyncio
async def test_rule_skipped_message_is_stored_without_llm_call(settings, quiet_console) -> None:
    store = SignalStore(settings.database_path)
    analyzer = StubAnalyzer(SignalAnalysis(is_valuable=True, score=9.0, category="Career"))
    processor = SignalProcessor(settings, store, analyzer, console=quiet_console)

    result = await processor.process(make_signal("good morning everyone"))

    assert result.status == "rule_skipped"
    assert analyzer.calls == 0
    rows = list(store.iter_all())
    assert len(rows) == 1
    assert rows[0].analysis.is_valuable is False


def test_unsent_saved_excludes_sent_signals(settings) -> None:
    store = SignalStore(settings.database_path)
    signal = make_signal("Remote AI Engineer role with Python, RAG, LangGraph and tracing.")
    analysis = SignalAnalysis(is_valuable=True, score=8.0, category="Career")

    stored_id = store.save(signal, analysis, saved_to_telegram=False)

    assert len(store.unsent_saved()) == 1
    assert len(store.recent_saved()) == 0

    store.mark_saved_to_telegram(stored_id)

    assert len(store.unsent_saved()) == 0
    assert len(store.recent_saved()) == 1
