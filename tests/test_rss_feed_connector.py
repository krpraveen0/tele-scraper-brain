from __future__ import annotations

from pathlib import Path

from app.models import SignalAnalysis, TelegramSignal
from app.rss_feed_connector import (
    FeedRegistry,
    FeedSource,
    clean_text,
    feed_rows,
    feed_source_registry,
    parse_feed_text,
    stable_message_id,
)


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>AI Engineering Feed</title>
    <link>https://example.com</link>
    <description>Example feed</description>
    <item>
      <title>Agent Context Patterns</title>
      <link>https://example.com/agent-context</link>
      <description>How teams manage context in real workflows.</description>
      <pubDate>Wed, 01 Jul 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Better RAG Evaluation</title>
      <link>https://example.com/rag-eval</link>
      <description>Practical RAG evaluation notes.</description>
      <pubDate>Wed, 01 Jul 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_feed_registry_loads_yaml(tmp_path: Path) -> None:
    path = tmp_path / "feeds.yaml"
    path.write_text(
        """
feeds:
  - name: OpenAI Blog
    url: https://openai.com/blog/rss.xml
    enabled: true
    trust_score: 8.5
    category_hint: AI Engineering
    min_save_score: 7.5
    destination: ai-engineering
    notes: High signal source
""".strip(),
        encoding="utf-8",
    )

    registry = FeedRegistry.from_yaml(path)

    assert len(registry.feeds) == 1
    feed = registry.feeds[0]
    assert feed.name == "OpenAI Blog"
    assert feed.url == "https://openai.com/blog/rss.xml"
    assert feed.enabled is True
    assert feed.trust_score == 8.5
    assert feed.category_hint == "AI Engineering"
    assert feed.min_save_score == 7.5
    assert feed.destination == "ai_engineering"


def test_parse_feed_text_returns_telegram_signals() -> None:
    feed = FeedSource(name="AI Engineering Feed", url="https://example.com/rss.xml", category_hint="AI Engineering")

    signals = parse_feed_text(feed, SAMPLE_FEED, limit=1)

    assert len(signals) == 1
    signal = signals[0]
    assert isinstance(signal, TelegramSignal)
    assert signal.source_id == "rss:https://example.com/rss.xml"
    assert signal.source_title == "AI Engineering Feed"
    assert signal.permalink == "https://example.com/agent-context"
    assert signal.source_ref == "https://example.com/rss.xml"
    assert "Title: Agent Context Patterns" in signal.message_text
    assert "Category hint: AI Engineering" in signal.message_text
    assert "How teams manage context" in signal.message_text


def test_feed_source_registry_applies_feed_threshold_and_route() -> None:
    feed = FeedSource(
        name="Research Feed",
        url="https://example.com/research.xml",
        min_save_score=8.5,
        destination="research",
    )
    signal = parse_feed_text(feed, SAMPLE_FEED, limit=1)[0]
    registry = feed_source_registry(FeedRegistry([feed]))
    analysis = SignalAnalysis(category="AI Engineering", score=9.0, is_valuable=True)

    assert registry.min_score_for(signal, default_min_score=7.0) == 8.5
    assert registry.destination_key_for(signal, analysis) == "research"
    assert registry.destination_chat_for(signal, analysis, {"default": "default-chat", "research": "research-chat"}, "default-chat") == "research-chat"


def test_stable_message_id_is_repeatable() -> None:
    first = stable_message_id("https://example.com/post")
    second = stable_message_id("https://example.com/post")
    third = stable_message_id("https://example.com/other")

    assert first == second
    assert first != third
    assert isinstance(first, int)


def test_feed_rows_are_ui_friendly() -> None:
    registry = FeedRegistry([FeedSource(name="Feed", url="https://example.com/rss.xml", enabled=False)])
    rows = feed_rows(registry)

    assert rows == [
        {
            "enabled": False,
            "name": "Feed",
            "url": "https://example.com/rss.xml",
            "trust_score": 5.0,
            "category_hint": "Other",
            "min_save_score": "default",
            "destination": "default",
            "notes": "",
        }
    ]


def test_clean_text_removes_extra_whitespace() -> None:
    assert clean_text("hello\n\n   world") == "hello world"
