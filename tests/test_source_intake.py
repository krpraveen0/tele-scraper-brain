from __future__ import annotations

from pathlib import Path

from app.source_intake import (
    command_rows,
    configured_feed_rows,
    feed_candidate_rows,
    intake_commands,
    recommended_feed_candidates,
    scheduler_snippets,
)


def test_intake_commands_include_telegram_rss_scheduler_and_monitor() -> None:
    commands = intake_commands(limit=25, send=True)
    rows = command_rows(commands)

    assert any("app.main backfill --limit 25 --send" in row["command"] for row in rows)
    assert any("app.rss_cli backfill --feeds feeds.yaml --limit 25 --send" in row["command"] for row in rows)
    assert any("--fetch-articles --send" in row["command"] for row in rows)
    assert any("app.intake_scheduler_cli run-due" in row["command"] for row in rows)
    assert any("app.intake_scheduler_cli due" in row["command"] for row in rows)
    assert any("feed-specific thresholds" in row["purpose"] for row in rows)
    assert any(row["command"] == "python -m app.main monitor" for row in rows)
    assert any("recommend-sources" in row["command"] for row in rows)


def test_configured_feed_rows_loads_yaml(tmp_path: Path) -> None:
    feeds_path = tmp_path / "feeds.yaml"
    feeds_path.write_text(
        """
feeds:
  - name: Research Feed
    url: https://example.com/research.xml
    min_save_score: 8.5
    destination: research
""".strip(),
        encoding="utf-8",
    )

    rows = configured_feed_rows(str(feeds_path))

    assert rows[0]["name"] == "Research Feed"
    assert rows[0]["url"] == "https://example.com/research.xml"
    assert rows[0]["min_save_score"] == 8.5
    assert rows[0]["destination"] == "research"


def test_scheduler_snippets_include_scheduler_telegram_rss_and_monitor() -> None:
    snippets = scheduler_snippets(limit=30)

    assert "app.intake_scheduler_cli run-due" in snippets["scheduler_runner_every_hour"]
    assert "app.intake_scheduler_cli run-due --dry-run" in snippets["scheduler_runner_dry_run"]
    assert "app.intake_scheduler_cli due" in snippets["list_due_schedules"]
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
