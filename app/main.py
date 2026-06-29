from __future__ import annotations

import argparse
import asyncio

from rich.console import Console

from app.config import load_settings
from app.daily_briefing import build_daily_briefing
from app.llm_filter import OllamaFilter
from app.message_cleaner import clean_message
from app.models import SignalAnalysis, TelegramSignal
from app.rule_filter import should_send_to_llm
from app.storage import SignalStore
from app.telegram_client import TelegramSignalClient

console = Console()


async def run_monitor() -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    llm = OllamaFilter(settings.ollama_url, settings.ollama_model)
    telegram = TelegramSignalClient(settings)

    async def handle_signal(raw_signal: TelegramSignal) -> SignalAnalysis | None:
        cleaned_text = clean_message(raw_signal.message_text, settings.max_message_chars)
        signal = TelegramSignal(
            source_id=raw_signal.source_id,
            source_title=raw_signal.source_title,
            message_id=raw_signal.message_id,
            message_text=cleaned_text,
            message_date=raw_signal.message_date,
            permalink=raw_signal.permalink,
        )

        if store.exists(signal):
            console.print(f"[yellow]Duplicate skipped:[/yellow] {signal.source_title}#{signal.message_id}")
            return None

        rule_decision = should_send_to_llm(signal.message_text)
        if not rule_decision.should_analyze:
            analysis = SignalAnalysis.safe_default(rule_decision.reason)
            store.save(signal, analysis, saved_to_telegram=False)
            console.print(f"[dim]Rule skipped:[/dim] {rule_decision.reason}")
            return analysis

        console.print(f"[cyan]Analyzing:[/cyan] {signal.source_title}#{signal.message_id}")
        analysis = llm.analyze(signal.message_text)
        should_save = analysis.is_valuable and analysis.score >= settings.min_save_score
        stored_id = store.save(signal, analysis, saved_to_telegram=False)

        if should_save:
            await telegram.send_saved_signal(signal, analysis)
            if stored_id:
                store.mark_saved_to_telegram(stored_id)
            console.print(
                f"[green]Saved:[/green] {analysis.category} | score={analysis.score} | action={analysis.suggested_action}"
            )
        else:
            console.print(f"[dim]Ignored:[/dim] score={analysis.score} reason={analysis.reason}")

        return analysis

    await telegram.run_monitor(handle_signal)


async def run_briefing(send: bool) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    briefing = build_daily_briefing(store)
    console.print(briefing)

    if send:
        telegram = TelegramSignalClient(settings)
        await telegram.start()
        await telegram.send_briefing(briefing)
        await telegram.client.disconnect()
        console.print("[green]Briefing sent to Telegram.[/green]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Praveen Signal OS")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("monitor", help="Start Telegram monitoring")

    briefing_parser = subparsers.add_parser("briefing", help="Generate a daily briefing")
    briefing_parser.add_argument("--send", action="store_true", help="Send briefing to Telegram")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "monitor":
        asyncio.run(run_monitor())
        return

    if args.command == "briefing":
        asyncio.run(run_briefing(send=args.send))
        return

    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
