from __future__ import annotations

import sqlite3
from pathlib import Path

from app.publishing_queue import PublishingQueue, normalize_content_type, normalize_platform, normalize_status


def test_publishing_queue_table_is_created(tmp_path: Path) -> None:
    db_path = tmp_path / "signals.db"
    PublishingQueue(db_path)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()

    assert "publishing_queue" in {row[0] for row in rows}


def test_add_and_get_queue_item(tmp_path: Path) -> None:
    queue = PublishingQueue(tmp_path / "signals.db")

    item = queue.add_item(
        title="Signal to Blueprint article",
        platform="medium",
        content_type="medium_article",
        status="idea_captured",
        priority=2,
        source_signal_id=10,
        notes="Polish after adding diagram.",
    )
    loaded = queue.get_item(item.id)

    assert loaded == item
    assert item.title == "Signal to Blueprint article"
    assert item.platform == "medium"
    assert item.priority == 2
    assert "Signal to Blueprint" in item.render()


def test_list_items_can_filter_by_status_and_platform(tmp_path: Path) -> None:
    queue = PublishingQueue(tmp_path / "signals.db")
    queue.add_item("LinkedIn idea", platform="linkedin", content_type="linkedin_post", status="idea_captured")
    queue.add_item("Medium draft", platform="medium", content_type="medium_article", status="draft_started")

    idea_items = queue.list_items(status="idea_captured")
    medium_items = queue.list_items(platform="medium")

    assert [item.title for item in idea_items] == ["LinkedIn idea"]
    assert [item.title for item in medium_items] == ["Medium draft"]


def test_update_status_and_published_url(tmp_path: Path) -> None:
    queue = PublishingQueue(tmp_path / "signals.db")
    item = queue.add_item("Post", platform="linkedin", content_type="linkedin_post")

    updated = queue.update_status(item.id, "published", published_url="https://example.com/post")

    assert updated.status == "published"
    assert updated.published_url == "https://example.com/post"
    assert updated.updated_at >= item.updated_at


def test_normalizers_accept_human_friendly_values() -> None:
    assert normalize_status("ready to publish") == "ready_to_publish"
    assert normalize_platform("LinkedIn") == "linkedin"
    assert normalize_content_type("medium article") == "medium_article"


def test_invalid_status_is_rejected(tmp_path: Path) -> None:
    queue = PublishingQueue(tmp_path / "signals.db")

    try:
        queue.add_item("Bad", platform="medium", content_type="medium_article", status="unknown")
    except ValueError as exc:
        assert "Unsupported queue status" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid queue status")
