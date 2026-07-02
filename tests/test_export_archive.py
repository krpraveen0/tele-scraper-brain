from __future__ import annotations

from pathlib import Path

from app.export_archive import (
    ExportableContent,
    archive_asset,
    archive_content,
    archive_queue_item,
    build_export_filename,
    export_asset,
    export_content_to_markdown,
    export_queue_item,
    normalize_export_type,
    slugify,
)
from app.models import StoredAsset
from app.publishing_queue import QueueItem


def make_asset() -> StoredAsset:
    return StoredAsset(
        id=7,
        signal_id=3,
        asset_type="linkedin",
        title="Signal to Blueprint Workflow",
        body="In a real workflow, the trade-off is clarity versus speed.",
        rewritten=False,
        exported_path="",
        sent_to_telegram=False,
        created_at="2026-07-02T10:00:00+00:00",
        sent_at=None,
    )


def make_queue_item() -> QueueItem:
    return QueueItem(
        id=5,
        source_signal_id=3,
        idea_id=2,
        blueprint_id=1,
        title="Publish Signal Workflow",
        content_type="medium_article",
        platform="medium",
        status="ready_to_publish",
        priority=2,
        notes="Ready after quality gate.",
        published_url="",
        created_at="2026-07-02T10:00:00+00:00",
        updated_at="2026-07-02T10:30:00+00:00",
    )


def test_export_content_to_markdown(tmp_path: Path) -> None:
    content = ExportableContent(
        title="My Draft",
        body="Draft body",
        content_type="draft",
        source_id=10,
        metadata={"surface": "linkedin"},
    )

    path = export_content_to_markdown(content, tmp_path)
    text = path.read_text(encoding="utf-8")

    assert path.name == "draft-10-my-draft.md"
    assert "content_type: draft" in text
    assert "surface: linkedin" in text
    assert "# My Draft" in text
    assert "Draft body" in text


def test_archive_content_writes_date_based_file(tmp_path: Path) -> None:
    content = ExportableContent(title="Archive Me", body="Body", content_type="note")

    record = archive_content(content, tmp_path, reason="No longer active.")
    text = record.path.read_text(encoding="utf-8")

    assert record.path.exists()
    assert record.path.parent.name == "note"
    assert record.reason == "No longer active."
    assert "archived: true" in text
    assert "archive_reason: No longer active." in text
    assert "# Archive Me" in text


def test_export_and_archive_asset(tmp_path: Path) -> None:
    asset = make_asset()

    exported = export_asset(asset, tmp_path / "exports")
    record = archive_asset(asset, tmp_path / "archive", reason="Published elsewhere.")

    assert exported.name.startswith("asset-7-signal-to-blueprint-workflow")
    assert "asset_id: 7" in exported.read_text(encoding="utf-8")
    assert record.content_type == "asset"
    assert "Published elsewhere." in record.path.read_text(encoding="utf-8")


def test_export_and_archive_queue_item(tmp_path: Path) -> None:
    item = make_queue_item()

    exported = export_queue_item(item, tmp_path / "exports")
    record = archive_queue_item(item, tmp_path / "archive", reason="Moved to backlog.")

    exported_text = exported.read_text(encoding="utf-8")
    assert exported.name.startswith("queue-item-5-publish-signal-workflow")
    assert "queue_item_id: 5" in exported_text
    assert "status: ready_to_publish" in exported_text
    assert record.content_type == "queue_item"
    assert "Moved to backlog." in record.path.read_text(encoding="utf-8")


def test_filename_helpers_are_safe() -> None:
    assert slugify("A/B: C++ Workflow!!!") == "a-b-c-workflow"
    filename = build_export_filename(ExportableContent(title="Hello World", body="Body", content_type="quality_report"))
    assert filename == "quality-report-hello-world.md"


def test_invalid_export_type_is_rejected() -> None:
    try:
        normalize_export_type("unknown")
    except ValueError as exc:
        assert "Unsupported export type" in str(exc)
        assert "asset" in str(exc)
    else:
        raise AssertionError("Expected invalid export type to fail")
