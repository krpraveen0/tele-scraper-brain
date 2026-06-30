from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from rich.console import Console

from app.config import Settings
from app.llm_provider import SignalAnalyzer
from app.message_cleaner import clean_message
from app.models import SignalAnalysis, TelegramSignal
from app.rule_filter import should_send_to_llm
from app.storage import SignalStore

SaveCallback = Callable[[TelegramSignal, SignalAnalysis], Awaitable[None]]


@dataclass(frozen=True)
class ProcessedSignal:
    signal: TelegramSignal
    analysis: SignalAnalysis | None
    status: str
    saved_to_telegram: bool = False


class SignalProcessor:
    """Shared processing pipeline for live monitoring and historical backfills."""

    def __init__(
        self,
        settings: Settings,
        store: SignalStore,
        analyzer: SignalAnalyzer,
        console: Console | None = None,
    ) -> None:
        self.settings = settings
        self.store = store
        self.analyzer = analyzer
        self.console = console or Console()

    async def process(
        self,
        raw_signal: TelegramSignal,
        send_saved_signal: SaveCallback | None = None,
    ) -> ProcessedSignal:
        signal = self._clean_signal(raw_signal)

        if self.store.exists(signal):
            self.console.print(f"[yellow]Duplicate skipped:[/yellow] {signal.source_title}#{signal.message_id}")
            return ProcessedSignal(signal=signal, analysis=None, status="duplicate")

        rule_decision = should_send_to_llm(signal.message_text)
        if not rule_decision.should_analyze:
            analysis = SignalAnalysis.safe_default(rule_decision.reason)
            self.store.save(signal, analysis, saved_to_telegram=False)
            self.console.print(f"[dim]Rule skipped:[/dim] {rule_decision.reason}")
            return ProcessedSignal(signal=signal, analysis=analysis, status="rule_skipped")

        self.console.print(
            f"[cyan]Analyzing with {self.settings.llm_provider}:[/cyan] {signal.source_title}#{signal.message_id}"
        )
        analysis = self.analyzer.analyze(signal.message_text)
        should_save = analysis.is_valuable and analysis.score >= self.settings.min_save_score
        stored_id = self.store.save(signal, analysis, saved_to_telegram=False)

        if should_save:
            if send_saved_signal is not None:
                await send_saved_signal(signal, analysis)
                if stored_id:
                    self.store.mark_saved_to_telegram(stored_id)
                self.console.print(
                    f"[green]Saved:[/green] {analysis.category} | score={analysis.score} | action={analysis.suggested_action}"
                )
                return ProcessedSignal(signal=signal, analysis=analysis, status="saved", saved_to_telegram=True)

            self.console.print(
                f"[green]Saved locally:[/green] {analysis.category} | score={analysis.score} | action={analysis.suggested_action}"
            )
            return ProcessedSignal(signal=signal, analysis=analysis, status="saved_local", saved_to_telegram=False)

        self.console.print(f"[dim]Ignored:[/dim] score={analysis.score} reason={analysis.reason}")
        return ProcessedSignal(signal=signal, analysis=analysis, status="ignored")

    def _clean_signal(self, raw_signal: TelegramSignal) -> TelegramSignal:
        cleaned_text = clean_message(raw_signal.message_text, self.settings.max_message_chars)
        return TelegramSignal(
            source_id=raw_signal.source_id,
            source_title=raw_signal.source_title,
            message_id=raw_signal.message_id,
            message_text=cleaned_text,
            message_date=raw_signal.message_date,
            permalink=raw_signal.permalink,
        )
