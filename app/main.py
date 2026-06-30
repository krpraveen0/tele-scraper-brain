from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from app.asset_exporter import export_asset_to_markdown
from app.asset_generator import ALLOWED_ASSET_TYPES, generate_asset
from app.asset_rewriter import create_asset_rewriter
from app.config import load_settings
from app.daily_briefing import build_daily_briefing
from app.llm_provider import create_analyzer
from app.models import ALLOWED_FEEDBACK_LABELS, FeedbackEntry, StoredAsset, StoredSignal, TelegramSignal
from app.signal_processor import SignalProcessor
from app.source_recommender import recommend_sources
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
            destination_key = settings.source_registry.destination_key_for(signal, stored.analysis)
            console.print(
                f"[green]Sent:[/green] {stored.analysis.category} | score={stored.analysis.score} | route={destination_key} | source={stored.source_title}"
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

    _print_signal_table(f"Recent saved signals ({len(signals)})", signals)


def run_unsent(limit: int) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    signals = store.unsent_saved(limit=limit)

    if not signals:
        console.print("[yellow]No unsent saved signals found.[/yellow]")
        return

    _print_signal_table(f"Unsent saved signals ({len(signals)})", signals)


def run_sources() -> None:
    settings = load_settings()
    sources = settings.source_registry.sources

    table = Table(title=f"Configured sources from {settings.sources_config_path}")
    table.add_column("Enabled")
    table.add_column("Name")
    table.add_column("Handle")
    table.add_column("Trust", justify="right")
    table.add_column("Hint")
    table.add_column("Min", justify="right")
    table.add_column("Route")

    for source in sources:
        table.add_row(
            "yes" if source.enabled else "no",
            source.name,
            source.handle,
            f"{source.trust_score:.1f}",
            source.category_hint,
            "default" if source.min_save_score is None else f"{source.min_save_score:.1f}",
            source.destination,
        )

    console.print(table)
    console.print(f"[dim]Enabled Telegram inputs: {', '.join(settings.source_chats)}[/dim]")


def run_stats() -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    rows = store.source_stats()

    if not rows:
        console.print("[yellow]No stored signals yet. Run backfill or monitor first.[/yellow]")
        return

    table = Table(title="Source quality report")
    table.add_column("Source")
    table.add_column("Total", justify="right")
    table.add_column("Useful", justify="right")
    table.add_column("Sent", justify="right")
    table.add_column("Avg", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Signal %", justify="right")
    table.add_column("Suggestion")

    for row in rows:
        total = int(row["total"] or 0)
        valuable = int(row["valuable"] or 0)
        sent = int(row["sent"] or 0)
        avg_score = float(row["avg_score"] or 0.0)
        max_score = float(row["max_score"] or 0.0)
        signal_ratio = (valuable / total * 100.0) if total else 0.0
        suggestion = _source_suggestion(total, valuable, avg_score, signal_ratio)
        table.add_row(
            str(row["source_title"]),
            str(total),
            str(valuable),
            str(sent),
            f"{avg_score:.1f}",
            f"{max_score:.1f}",
            f"{signal_ratio:.0f}%",
            suggestion,
        )

    console.print(table)
    console.print(f"[dim]Default minimum save score: {settings.min_save_score:.1f}[/dim]")


def run_recommend_sources(min_samples: int) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    rows = store.source_stats()

    if not rows:
        console.print("[yellow]No stored signals yet. Run backfill or monitor first.[/yellow]")
        return

    recommendations = recommend_sources(rows, min_samples=min_samples)
    table = Table(title="Source recommendations")
    table.add_column("Source")
    table.add_column("Action")
    table.add_column("Total", justify="right")
    table.add_column("Useful", justify="right")
    table.add_column("Signal %", justify="right")
    table.add_column("Avg", justify="right")
    table.add_column("Suggested Min", justify="right")
    table.add_column("Reason")

    for item in recommendations:
        suggested_min = "-" if item.suggested_min_save_score is None else f"{item.suggested_min_save_score:.1f}"
        table.add_row(
            item.source_title,
            item.action,
            str(item.total),
            str(item.valuable),
            f"{item.signal_ratio:.0f}%",
            f"{item.avg_score:.1f}",
            suggested_min,
            item.reason,
        )

    console.print(table)
    console.print(f"[dim]Minimum samples for recommendation: {min_samples}[/dim]")
    console.print("[dim]Edit sources.yaml manually using these suggestions; this command does not modify your config.[/dim]")


async def run_create_asset(
    signal_id: int,
    asset_type: str,
    rewrite: bool,
    save: bool,
    export: bool,
    export_dir: str | None,
    send: bool,
) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    signal = store.get_signal(signal_id)
    if signal is None:
        raise ValueError(f"Signal id {signal_id} does not exist.")

    asset = generate_asset(signal, asset_type)
    rewritten = False
    if rewrite:
        rewriter = create_asset_rewriter(settings)
        asset = rewriter.rewrite(signal, asset)
        rewritten = True

    stored_asset = None
    should_save = save or export or send
    if should_save:
        stored_asset = store.save_asset(asset, rewritten=rewritten)
        console.print(f"[green]Asset saved:[/green] asset_id={stored_asset.id} | signal_id={stored_asset.signal_id} | type={stored_asset.asset_type}")

    if export:
        assert stored_asset is not None
        target_dir = Path(export_dir) if export_dir else settings.asset_export_dir
        path = export_asset_to_markdown(stored_asset, target_dir)
        store.mark_asset_exported(stored_asset.id, path)
        stored_asset = store.get_asset(stored_asset.id) or stored_asset
        console.print(f"[green]Asset exported:[/green] {path}")

    if send:
        assert stored_asset is not None
        telegram = TelegramSignalClient(settings)
        await telegram.start()
        try:
            await telegram.send_asset(stored_asset)
            store.mark_asset_sent(stored_asset.id)
            console.print(f"[green]Asset sent to Telegram:[/green] asset_id={stored_asset.id} chat={settings.asset_chat}")
        finally:
            await telegram.disconnect()

    console.print(asset.render())


def run_assets(limit: int) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    assets = store.recent_assets(limit=limit)

    if not assets:
        console.print("[yellow]No generated assets found yet.[/yellow]")
        console.print("[dim]Use `python -m app.main create-asset --id <signal_id> --type linkedin --save` first.[/dim]")
        return

    _print_asset_table(f"Recent assets ({len(assets)})", assets)


def run_feedback(signal_id: int, label: str, notes: str) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    feedback = store.add_feedback(signal_id=signal_id, label=label, notes=notes)
    console.print(
        f"[green]Feedback saved:[/green] signal_id={feedback.signal_id} | label={feedback.label} | feedback_id={feedback.id}"
    )
    if feedback.notes:
        console.print(f"[dim]Notes:[/dim] {feedback.notes}")


def run_feedback_summary() -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    rows = store.feedback_summary()

    if not rows:
        console.print("[yellow]No feedback labels found yet.[/yellow]")
        console.print("[dim]Use `python -m app.main feedback --id <signal_id> --label useful` first.[/dim]")
        return

    table = Table(title="Feedback summary")
    table.add_column("Label")
    table.add_column("Count", justify="right")
    table.add_column("Avg Score", justify="right")
    table.add_column("Sent", justify="right")

    for row in rows:
        table.add_row(
            str(row["label"]),
            str(row["count"]),
            f"{float(row['avg_score'] or 0.0):.1f}",
            str(row["sent"] or 0),
        )

    console.print(table)


def run_feedback_recent(limit: int) -> None:
    settings = load_settings()
    store = SignalStore(settings.database_path)
    entries = store.recent_feedback(limit=limit)

    if not entries:
        console.print("[yellow]No feedback labels found yet.[/yellow]")
        return

    _print_feedback_table(f"Recent feedback ({len(entries)})", entries)


def _source_suggestion(total: int, valuable: int, avg_score: float, signal_ratio: float) -> str:
    if total >= 20 and signal_ratio < 5:
        return "raise threshold / disable"
    if total >= 10 and signal_ratio > 40 and avg_score >= 6.5:
        return "high-value source"
    if valuable == 0:
        return "watch"
    return "keep testing"


def _print_signal_table(title: str, signals: list[StoredSignal]) -> None:
    table = Table(title=title)
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Score", justify="right")
    table.add_column("Category")
    table.add_column("Action")
    table.add_column("Source")
    table.add_column("Summary")

    for signal in signals:
        summary = signal.analysis.summary or signal.analysis.reason or signal.message_text[:120]
        if len(summary) > 120:
            summary = f"{summary[:117]}..."
        table.add_row(
            str(signal.id),
            f"{signal.analysis.score:.1f}",
            signal.analysis.category,
            signal.analysis.suggested_action,
            signal.source_title,
            summary,
        )

    console.print(table)


def _print_feedback_table(title: str, entries: list[FeedbackEntry]) -> None:
    table = Table(title=title)
    table.add_column("Feedback ID", justify="right", style="dim")
    table.add_column("Signal ID", justify="right")
    table.add_column("Label")
    table.add_column("Notes")
    table.add_column("Created")

    for entry in entries:
        notes = entry.notes
        if len(notes) > 80:
            notes = f"{notes[:77]}..."
        table.add_row(str(entry.id), str(entry.signal_id), entry.label, notes, entry.created_at)

    console.print(table)


def _print_asset_table(title: str, assets: list[StoredAsset]) -> None:
    table = Table(title=title)
    table.add_column("Asset ID", justify="right", style="dim")
    table.add_column("Signal ID", justify="right")
    table.add_column("Type")
    table.add_column("Rewritten")
    table.add_column("Exported")
    table.add_column("Sent")
    table.add_column("Title")

    for asset in assets:
        table.add_row(
            str(asset.id),
            str(asset.signal_id),
            asset.asset_type,
            "yes" if asset.rewritten else "no",
            asset.exported_path or "-",
            "yes" if asset.sent_to_telegram else "no",
            asset.title,
        )

    console.print(table)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Praveen Signal OS")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("monitor", help="Start Telegram monitoring")
    subparsers.add_parser("sources", help="Show configured sources and routing metadata")
    subparsers.add_parser("stats", help="Show source quality statistics")

    recommend_parser = subparsers.add_parser("recommend-sources", help="Recommend source tuning actions from local stats")
    recommend_parser.add_argument("--min-samples", type=int, default=10, help="Minimum processed messages before tuning a source")

    asset_parser = subparsers.add_parser("create-asset", help="Create a reusable asset draft from a saved signal")
    asset_parser.add_argument("--id", type=int, required=True, help="Signal ID from recent or unsent table")
    asset_parser.add_argument("--type", required=True, choices=sorted(ALLOWED_ASSET_TYPES), help="Asset type to generate")
    asset_parser.add_argument("--rewrite", action="store_true", help="Rewrite the generated asset with the configured LLM backend")
    asset_parser.add_argument("--save", action="store_true", help="Save the generated asset to SQLite history")
    asset_parser.add_argument("--export", action="store_true", help="Export the generated asset as Markdown")
    asset_parser.add_argument("--export-dir", default=None, help="Markdown export directory. Defaults to ASSET_EXPORT_DIR")
    asset_parser.add_argument("--send", action="store_true", help="Send the generated asset to Telegram")

    assets_parser = subparsers.add_parser("assets", help="Show recent generated assets")
    assets_parser.add_argument("--limit", type=int, default=20, help="Number of assets to show")

    feedback_parser = subparsers.add_parser("feedback", help="Attach feedback label to a saved signal")
    feedback_parser.add_argument("--id", type=int, required=True, help="Signal ID from recent or unsent table")
    feedback_parser.add_argument("--label", required=True, choices=sorted(ALLOWED_FEEDBACK_LABELS), help="Feedback label")
    feedback_parser.add_argument("--notes", default="", help="Optional feedback notes")

    subparsers.add_parser("feedback-summary", help="Show feedback label counts")

    feedback_recent_parser = subparsers.add_parser("feedback-recent", help="Show recent feedback labels")
    feedback_recent_parser.add_argument("--limit", type=int, default=20, help="Number of recent feedback entries to show")

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

    if args.command == "sources":
        run_sources()
        return

    if args.command == "stats":
        run_stats()
        return

    if args.command == "recommend-sources":
        if args.min_samples < 1:
            raise RuntimeError("--min-samples must be at least 1")
        run_recommend_sources(min_samples=args.min_samples)
        return

    if args.command == "create-asset":
        if args.id < 1:
            raise RuntimeError("--id must be at least 1")
        asyncio.run(
            run_create_asset(
                signal_id=args.id,
                asset_type=args.type,
                rewrite=args.rewrite,
                save=args.save,
                export=args.export,
                export_dir=args.export_dir,
                send=args.send,
            )
        )
        return

    if args.command == "assets":
        if args.limit < 1:
            raise RuntimeError("--limit must be at least 1")
        run_assets(limit=args.limit)
        return

    if args.command == "feedback":
        if args.id < 1:
            raise RuntimeError("--id must be at least 1")
        run_feedback(signal_id=args.id, label=args.label, notes=args.notes)
        return

    if args.command == "feedback-summary":
        run_feedback_summary()
        return

    if args.command == "feedback-recent":
        if args.limit < 1:
            raise RuntimeError("--limit must be at least 1")
        run_feedback_recent(limit=args.limit)
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
