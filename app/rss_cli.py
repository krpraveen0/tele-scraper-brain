from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from rich.console import Console
from rich.table import Table

from app.config import load_settings
from app.llm_provider import create_analyzer
from app.rss_feed_connector import FeedRegistry, feed_rows, fetch_feed_signals, settings_with_feed_routing
from app.signal_processor import SignalProcessor
from app.storage import SignalStore
from app.telegram_client import TelegramSignalClient

console = Console()


async def run_rss_backfill(feeds_path: str, limit: int, fetch_articles: bool, send: bool) -> None:
    base_settings = load_settings()
    registry = FeedRegistry.from_yaml(Path(feeds_path))
    feeds = registry.enabled_feeds()
    if not feeds:
        console.print(f"[yellow]No enabled feeds found in {feeds_path}.[/yellow]")
        return

    settings = settings_with_feed_routing(base_settings, registry)
    store = SignalStore(settings.database_path)
    analyzer = create_analyzer(settings)
    processor = SignalProcessor(settings=settings, store=store, analyzer=analyzer, console=console)
    telegram = TelegramSignalClient(settings) if send else None

    console.print(f"[bold]RSS backfill:[/bold] feeds={len(feeds)} limit={limit} fetch_articles={fetch_articles} send={send}")
    console.print("[dim]Feed-specific min_save_score and destination routing are active.[/dim]")
    signals = await fetch_feed_signals(feeds, limit_per_feed=limit, fetch_articles=fetch_articles)

    if telegram:
        await telegram.start()

    counts = {"processed": 0, "saved": 0, "saved_local": 0, "ignored": 0, "rule_skipped": 0, "duplicate": 0}
    try:
        for signal in signals:
            callback = telegram.send_saved_signal if telegram else None
            result = await processor.process(signal, send_saved_signal=callback)
            counts["processed"] += 1
            counts[result.status] = counts.get(result.status, 0) + 1
    finally:
        if telegram:
            await telegram.disconnect()

    console.print("[bold green]RSS backfill complete[/bold green]")
    console.print(
        "Processed={processed} | Saved={saved} | Saved local={saved_local} | Ignored={ignored} | Rule skipped={rule_skipped} | Duplicates={duplicate}".format(
            **counts
        )
    )


def run_feeds(feeds_path: str) -> None:
    registry = FeedRegistry.from_yaml(Path(feeds_path))
    rows = feed_rows(registry)
    if not rows:
        console.print(f"[yellow]No feeds found in {feeds_path}. Copy feeds.example.yaml to feeds.yaml first.[/yellow]")
        return

    table = Table(title=f"Configured RSS feeds from {feeds_path}")
    table.add_column("Enabled")
    table.add_column("Name")
    table.add_column("URL")
    table.add_column("Trust", justify="right")
    table.add_column("Hint")
    table.add_column("Min", justify="right")
    table.add_column("Route")

    for row in rows:
        table.add_row(
            "yes" if row["enabled"] else "no",
            str(row["name"]),
            str(row["url"]),
            f"{float(row['trust_score']):.1f}",
            str(row["category_hint"]),
            str(row["min_save_score"]),
            str(row["destination"]),
        )
    console.print(table)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RSS/blog feed intake for Praveen Signal OS")
    subparsers = parser.add_subparsers(dest="command", required=True)

    feeds_parser = subparsers.add_parser("feeds", help="Show configured RSS/blog feeds")
    feeds_parser.add_argument("--feeds", default="feeds.yaml", help="Path to feeds.yaml")

    backfill_parser = subparsers.add_parser("backfill", help="Fetch and analyze recent RSS/blog feed entries")
    backfill_parser.add_argument("--feeds", default="feeds.yaml", help="Path to feeds.yaml")
    backfill_parser.add_argument("--limit", type=int, default=10, help="Number of entries per feed")
    backfill_parser.add_argument("--fetch-articles", action="store_true", help="Fetch and extract full article text with Trafilatura")
    backfill_parser.add_argument("--send", action="store_true", help="Forward saved signals to Telegram destination")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "feeds":
        run_feeds(feeds_path=args.feeds)
        return
    if args.command == "backfill":
        if args.limit < 1:
            raise RuntimeError("--limit must be at least 1")
        asyncio.run(run_rss_backfill(feeds_path=args.feeds, limit=args.limit, fetch_articles=args.fetch_articles, send=args.send))
        return
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
