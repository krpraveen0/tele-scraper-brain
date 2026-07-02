from __future__ import annotations

from app.source_intake import (
    command_rows,
    feed_candidate_rows,
    intake_commands,
    recommended_feed_candidates,
    scheduler_snippets,
)


def test_intake_commands_include_telegram_rss_and_monitor() -> None:
    commands = intake_commands(limit=25, send=True)
    rows = command_rows(commands)

    assert any("app.main backfill --limit 25 --send" in row["command"] for row in rows)
    assert any("app.rss_cli backfill --feeds feeds.yaml --limit 25 --send" in row["command"] for row in rows)
    assert any("--fetch-articles --send" in row["command"] for row in rows)
    assert any(row["command"] == "python -m app.main monitor" for row in rows)
    assert any("recommend-sources" in row["command"] for row in rows)


def test_scheduler_snippets_include_telegram_rss_and_monitor() -> None:
    snippets = scheduler_snippets(limit=30)

    assert "app.main backfill --limit 30" in snippets["telegram_cron_every_2_hours"]
    assert "app.rss_cli backfill --feeds feeds.yaml --limit 30" in snippets["rss_cron_every_4_hours"]
    assert "python -m app.main monitor" in snippets["manual_telegram_monitor"]


def test_recommended_feed_candidates_are_practical_for_user_goals() -> None:
    candidates = recommended_feed_candidates()
    rows = feed_candidate_rows()

    names = {candidate.name for candidate in candidates}
    categories = {candidate.category for candidate in candidates}

    assert "OpenAI Blog" in names
    assert "Anthropic Engineering" in names
    assert "GitHub Blog - AI & ML" in names
    assert "AI Engineering" in categories
    assert "Research" in categories
    assert len(rows) == len(candidates)
    assert all(row["url"].startswith("https://") for row in rows)
