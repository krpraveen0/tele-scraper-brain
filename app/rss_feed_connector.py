from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

import feedparser
import httpx
import trafilatura
import yaml

from app.models import TelegramSignal
from app.sources import normalize_destination_key


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str
    enabled: bool = True
    trust_score: float = 5.0
    category_hint: str = "Other"
    min_save_score: float | None = None
    destination: str = "default"
    notes: str = ""

    @property
    def source_id(self) -> str:
        return f"rss:{self.url}"


class FeedRegistry:
    def __init__(self, feeds: list[FeedSource]) -> None:
        self.feeds = feeds

    @classmethod
    def empty(cls) -> "FeedRegistry":
        return cls([])

    @classmethod
    def from_yaml(cls, path: Path) -> "FeedRegistry":
        if not path.exists():
            return cls.empty()

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        raw_feeds = data.get("feeds", [])
        if not isinstance(raw_feeds, list):
            raise RuntimeError(f"{path} must contain a top-level 'feeds' list.")

        feeds: list[FeedSource] = []
        for index, item in enumerate(raw_feeds, start=1):
            if not isinstance(item, dict):
                raise RuntimeError(f"Feed entry #{index} in {path} must be a mapping.")
            url = str(item.get("url", "") or "").strip()
            if not url:
                raise RuntimeError(f"Feed entry #{index} in {path} must include a url.")
            name = str(item.get("name", "") or url).strip()
            feeds.append(
                FeedSource(
                    name=name,
                    url=url,
                    enabled=bool(item.get("enabled", True)),
                    trust_score=_clamp(item.get("trust_score", 5.0)),
                    category_hint=str(item.get("category_hint", "Other") or "Other").strip(),
                    min_save_score=_optional_float(item.get("min_save_score")),
                    destination=normalize_destination_key(str(item.get("destination", "default") or "default")),
                    notes=str(item.get("notes", "") or "").strip(),
                )
            )
        return cls(feeds)

    def enabled_feeds(self) -> list[FeedSource]:
        return [feed for feed in self.feeds if feed.enabled]


def parse_feed_text(feed: FeedSource, feed_text: str, limit: int = 20) -> list[TelegramSignal]:
    parsed = feedparser.parse(feed_text)
    signals: list[TelegramSignal] = []
    for entry in parsed.entries[:limit]:
        signals.append(entry_to_signal(feed, entry, article_text=""))
    return signals


async def fetch_feed_signals(
    feeds: list[FeedSource],
    limit_per_feed: int = 20,
    fetch_articles: bool = False,
    timeout_seconds: int = 30,
) -> list[TelegramSignal]:
    signals: list[TelegramSignal] = []
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        for feed in feeds:
            response = await client.get(feed.url)
            response.raise_for_status()
            parsed = feedparser.parse(response.text)
            for entry in parsed.entries[:limit_per_feed]:
                article_text = ""
                if fetch_articles:
                    article_text = await fetch_article_text(client, entry_link(entry))
                signals.append(entry_to_signal(feed, entry, article_text=article_text))
    return signals


async def fetch_article_text(client: httpx.AsyncClient, url: str) -> str:
    if not url:
        return ""
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPError:
        return ""
    extracted = trafilatura.extract(response.text, include_comments=False, include_tables=False, favor_precision=True)
    return str(extracted or "").strip()


def entry_to_signal(feed: FeedSource, entry: Any, article_text: str = "") -> TelegramSignal:
    title = clean_text(getattr(entry, "title", ""))
    link = entry_link(entry)
    summary = clean_text(getattr(entry, "summary", "") or getattr(entry, "description", ""))
    published = entry_datetime(entry)
    body_parts = [
        f"Title: {title}" if title else "",
        f"Source: {feed.name}",
        f"Category hint: {feed.category_hint}" if feed.category_hint else "",
        f"Link: {link}" if link else "",
        "",
        "Summary:",
        summary,
    ]
    if article_text:
        body_parts.extend(["", "Extracted article:", clean_text(article_text)])

    return TelegramSignal(
        source_id=feed.source_id,
        source_title=feed.name,
        message_id=stable_message_id(link or f"{feed.url}:{title}:{published.isoformat()}"),
        message_text="\n".join(part for part in body_parts if part is not None).strip(),
        message_date=published,
        permalink=link or None,
        source_ref=feed.url,
    )


def entry_link(entry: Any) -> str:
    return str(getattr(entry, "link", "") or getattr(entry, "id", "") or "").strip()


def entry_datetime(entry: Any) -> datetime:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def stable_message_id(value: str) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return int(digest, 16)


def clean_text(value: str) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def feed_rows(registry: FeedRegistry) -> list[dict[str, object]]:
    return [
        {
            "enabled": feed.enabled,
            "name": feed.name,
            "url": feed.url,
            "trust_score": feed.trust_score,
            "category_hint": feed.category_hint,
            "min_save_score": feed.min_save_score if feed.min_save_score is not None else "default",
            "destination": feed.destination,
            "notes": feed.notes,
        }
        for feed in registry.feeds
    ]


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return _clamp(value)


def _clamp(value: Any, default: float = 5.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(10.0, number))
