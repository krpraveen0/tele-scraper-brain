from __future__ import annotations

import argparse
import asyncio
from datetime import datetime

from rich.console import Console
from rich.table import Table

from app.config import load_settings
from app.daily_briefing import build_daily_briefing
from app.llm_provider import create_analyzer
from app.models import StoredSignal, TelegramSignal
from app.signal_processor import SignalProcessor
from app.storage import SignalStore
from app.telegram_client import TelegramSignalClient

console = Console()


def stored_to_telegram_signal(stored: StoredSignal) -> TelegramSignal:
    try:
        message_date = datetime.fromisoformat(stored.message_date)
    except ValueError:
        message_date = datetime.fromisoformat(stored.created_at)

    return TelegramSignal(
        source_id=stored.source_id,
        source_title=stored.source_title,
        message_id=stored.message_id,
        message_text=stored.message_text,
        message_date=message_date,
        permalink=stored.permalink,
    )


async def run_monitor() -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    analyzer = create_analyzer(settings)
    telegram = TelegramSignalClient(settings)
    processor = SignalProcessor(settings=settings, store=store, analyzer=analyzer, console=console)

    async def handle_signal(raw_signal):
        result = await processor.process(raw_signal, send_saved_signal=telegram.send_saved_signal)
        return result.analysis

    await telegram.run_monitor(handle_signal)


async def send_unsent_saved_signals(limit: int) -> int:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    telegram = TelegramSignalClient(settings)
    unsent = store.unsent_saved(limit=limit)

    if not unsent:
        console.print("[yellow]No unsent saved signals found.[/yellow]")
        return 0

    console.print(f"[bold]Sending {len(unsent)} previously saved unsent signal(s) to Telegram[/bold]")
    await telegram.start()
    try:
        for stored in unsent:
            signal = stored_to_telegram_signal(stored)
            await telegram.send_saved_signal(signal, stored.analysis)
            store.mark_saved_to_telegram(stored.id)
            console.print(
                f"[green]Sent:[/green] {stored.analysis.category} | score={stored.analysis.score} | source={stored.source_title}"
            )
    finally:
        await telegram.disconnect()

    return len(unsent)


async def run_backfill(limit: int, send: bool) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    analyzer = create_analyzer(settings)
    telegram = TelegramSignalClient(settings)
    processor = SignalProcessor(settings=settings, store=store, analyzer=analyzer, console=console)

    console.print(f"[bold]Backfilling last {limit} text messages per source[/bold]")
    if send:
        console.print("[yellow]Saved signals will be sent to Telegram.[/yellow]")
    else:
        console.print("[dim]Dry send mode: saved signals stay local. Use --send to forward saved signals.[/dim]")

    counts = {"processed": 0, "saved": 0, "saved_local": 0, "ignored": 0, "rule_skipped": 0, "duplicate": 0}

    try:
        async for signal in telegram.iter_recent_signals(limit_per_source=limit):
            callback = telegram.send_saved_signal if send else None
            result = await processor.process(signal, send_saved_signal=callback)
            counts["processed"] += 1
            counts[result.status] = counts.get(result.status, 0) + 1
    finally:
        await telegram.disconnect()

    sent_unsent = 0
    if send:
        # This handles the common flow: first backfill without --send, inspect locally,
        # then rerun with --send. The rerun sees duplicates, so we forward saved-but-unsent rows here.
        sent_unsent = await send_unsent_saved_signals(limit=limit * max(1, len(settings.source_chats)))

    console.print()
    console.print("[bold green]Backfill complete[/bold green]")
    console.print(
        "Processed={processed} | Saved={saved} | Saved local={saved_local} | Ignored={ignored} | Rule skipped={rule_skipped} | Duplicates={duplicate} | Sent unsent={sent_unsent}".format(
            sent_unsent=sent_unsent,
            **counts,
        )
    )


async def run_briefing(send: bool) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    briefing = build_daily_briefing(store)
    console.print(briefing)

    if send:
        telegram = TelegramSignalClient(settings)
        await telegram.start()
        await telegram.send_briefing(briefing)
        await telegram.disconnect()
        console.print("[green]Briefing sent to Telegram.[/green]")


def run_recent(limit: int) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    signals = store.recent_saved(limit=limit)

    if not signals:
        console.print("[yellow]No saved signals found yet.[/yellow]")
        console.print("[dim]If you ran backfill without --send, use `python -m app.main unsent` to review local saved items.[/dim]")
        return

    table = Table(title=f"Recent saved signals ({len(signals)})")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Score", justify="right")
    table.add_column("Category")
    table.add_column("Action")
    table.add_column("Source")
    table.add_column("Summary")

    for index, signal in enumerate(signals, start=1):
        summary = signal.analysis.summary or signal.analysis.reason or signal.message_text[:120]
        if len(summary) > 120:
            summary = f"{summary[:117]}..."
        table.add_row(
            str(index),
            f"{signal.analysis.score:.1f}",
            signal.analysis.category,
            signal.analysis.suggested_action,
            signal.source_title,
            summary,
        )

    console.print(table)


def run_unsent(limit: int) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    signals = store.unsent_saved(limit=limit)

    if not signals:
        console.print("[yellow]No unsent saved signals found.[/yellow]")
        return

    table = Table(title=f"Unsent saved signals ({len(signals)})")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Score", justify="right")
    table.add_column("Category")
    table.add_column("Action")
    table.add_column("Source")
    table.add_column("Summary")

    for index, signal in enumerate(signals, start=1):
        summary = signal.analysis.summary or signal.analysis.reason or signal.message_text[:120]
        if len(summary) > 120:
            summary = f"{summary[:117]}..."
        table.add_row(
            str(index),
            f"{signal.analysis.score:.1f}",
            signal.analysis.category,
            signal.analysis.suggested_action,
            signal.source_title,
            summary,
        )

    console.print(table)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Praveen Signal OS")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("monitor", help="Start Telegram monitoring")

    backfill_parser = subparsers.add_parser("backfill", help="Process recent historical Telegram messages")
    backfill_parser.add_argument("--limit", type=int, default=20, help="Number of recent text messages per source")
    backfill_parser.add_argument("--send", action="store_true", help="Forward saved signals to Telegram")

    recent_parser = subparsers.add_parser("recent", help="Show recent sent saved signals from local storage")
    recent_parser.add_argument("--limit", type=int, default=20, help="Number of sent saved signals to show")

    unsent_parser = subparsers.add_parser("unsent", help="Show locally saved signals not yet sent to Telegram")
    unsent_parser.add_argument("--limit", type=int, default=20, help="Number of unsent saved signals to show")

    send_unsent_parser = subparsers.add_parser("send-unsent", help="Send locally saved unsent signals to Telegram")
    send_unsent_parser.add_argument("--limit", type=int, default=20, help="Number of unsent saved signals to send")

    briefing_parser = subparsers.add_parser("briefing", help="Generate a daily briefing")
    briefing_parser.add_argument("--send", action="store_true", help="Send briefing to Telegram")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "monitor":
        asyncio.run(run_monitor())
        return

    if args.command == "backfill":
        if args.limit < 1:
            raise RuntimeError("--limit must be at least 1")
        asyncio.run(run_backfill(limit=args.limit, send=args.send))
        return

    if args.command == "recent":
        if args.limit < 1:
            raise RuntimeError("--limit must be at least 1")
        run_recent(limit=args.limit)
        return

    if args.command == "unsent":
        if args.limit < 1:
            raise RuntimeError("--limit must be at least 1")
        run_unsent(limit=args.limit)
        return

    if args.command == "send-unsent":
        if args.limit < 1:
            raise RuntimeError("--limit must be at least 1")
        asyncio.run(send_unsent_saved_signals(limit=args.limit))
        return

    if args.command == "briefing":
        asyncio.run(run_briefing(send=args.send))
        return

    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
