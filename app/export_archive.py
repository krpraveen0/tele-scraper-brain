from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

from app.models import StoredAsset, utc_now_iso
from app.publishing_queue import QueueItem


ALLOWED_EXPORT_TYPES = {
    "asset",
    "queue_item",
    "quality_report",
    "draft",
    "note",
}

SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class ExportableContent:
    title: str
    body: str
    content_type: str = "draft"
    source_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        title = self.title.strip() or "Untitled"
        body = self.body.strip()
        return f"# {title}\n\n{body}".strip()


@dataclass(frozen=True)
class ArchiveRecord:
    path: Path
    title: str
    content_type: str
    archived_at: str
    reason: str
    metadata: dict[str, Any]

    def render(self) -> str:
        lines = [
            f"# Archive Record: {self.title}",
            "",
            f"Path: {self.path}",
            f"Content type: {self.content_type}",
            f"Archived at: {self.archived_at}",
            f"Reason: {self.reason or '-'}",
            "",
            "## Metadata",
        ]
        if self.metadata:
            lines.extend(f"- {key}: {value}" for key, value in sorted(self.metadata.items()))
        else:
            lines.append("- none")
        return "\n".join(lines).strip()


def normalize_export_type(value: str) -> str:
    normalized = str(value or "draft").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_EXPORT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_EXPORT_TYPES))
        raise ValueError(f"Unsupported export type '{value}'. Allowed types: {allowed}")
    return normalized


def export_content_to_markdown(content: ExportableContent, export_dir: Path) -> Path:
    export_type = normalize_export_type(content.content_type)
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = build_export_filename(content)
    path = export_dir / filename
    path.write_text(render_markdown_document(content, archived=False), encoding="utf-8")
    return path


def archive_content(content: ExportableContent, archive_root: Path, reason: str = "") -> ArchiveRecord:
    export_type = normalize_export_type(content.content_type)
    archived_at = utc_now_iso()
    archive_dir = archive_root / archived_at[:10] / export_type
    archive_dir.mkdir(parents=True, exist_ok=True)
    path = archive_dir / build_export_filename(content)
    path.write_text(render_markdown_document(content, archived=True, archived_at=archived_at, reason=reason), encoding="utf-8")
    return ArchiveRecord(
        path=path,
        title=content.title.strip() or "Untitled",
        content_type=export_type,
        archived_at=archived_at,
        reason=reason.strip(),
        metadata=content.metadata,
    )


def export_asset(asset: StoredAsset, export_dir: Path) -> Path:
    return export_content_to_markdown(asset_to_exportable(asset), export_dir)


def archive_asset(asset: StoredAsset, archive_root: Path, reason: str = "") -> ArchiveRecord:
    return archive_content(asset_to_exportable(asset), archive_root, reason=reason)


def export_queue_item(item: QueueItem, export_dir: Path) -> Path:
    return export_content_to_markdown(queue_item_to_exportable(item), export_dir)


def archive_queue_item(item: QueueItem, archive_root: Path, reason: str = "") -> ArchiveRecord:
    return archive_content(queue_item_to_exportable(item), archive_root, reason=reason)


def asset_to_exportable(asset: StoredAsset) -> ExportableContent:
    return ExportableContent(
        title=asset.title,
        body=asset.body,
        content_type="asset",
        source_id=asset.id,
        metadata={
            "asset_id": asset.id,
            "signal_id": asset.signal_id,
            "asset_type": asset.asset_type,
            "rewritten": str(asset.rewritten).lower(),
            "sent_to_telegram": str(asset.sent_to_telegram).lower(),
            "created_at": asset.created_at,
        },
    )


def queue_item_to_exportable(item: QueueItem) -> ExportableContent:
    return ExportableContent(
        title=item.title,
        body=item.render(),
        content_type="queue_item",
        source_id=item.id,
        metadata={
            "queue_item_id": item.id,
            "status": item.status,
            "platform": item.platform,
            "content_type": item.content_type,
            "priority": item.priority,
            "source_signal_id": item.source_signal_id or "",
            "idea_id": item.idea_id or "",
            "blueprint_id": item.blueprint_id or "",
            "published_url": item.published_url,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        },
    )


def build_export_filename(content: ExportableContent) -> str:
    export_type = normalize_export_type(content.content_type)
    prefix = export_type.replace("_", "-")
    source_part = f"-{content.source_id}" if content.source_id is not None else ""
    return f"{prefix}{source_part}-{slugify(content.title)}.md"


def render_markdown_document(
    content: ExportableContent,
    archived: bool = False,
    archived_at: str = "",
    reason: str = "",
) -> str:
    export_type = normalize_export_type(content.content_type)
    metadata = {
        "content_type": export_type,
        "source_id": content.source_id or "",
        "title": content.title.strip() or "Untitled",
        "archived": str(archived).lower(),
        **content.metadata,
    }
    if archived:
        metadata["archived_at"] = archived_at
        metadata["archive_reason"] = reason.strip()

    front_matter = ["---"]
    for key, value in sorted(metadata.items()):
        front_matter.append(f"{key}: {format_metadata_value(value)}")
    front_matter.append("---")
    return "\n".join(front_matter) + "\n\n" + content.render() + "\n"


def format_metadata_value(value: Any) -> str:
    text = str(value).replace("\n", " ").strip()
    if not text:
        return "''"
    if any(char in text for char in [":", "#", "{", "}", "[", "]", ","]):
        return repr(text)
    return text


def slugify(value: str) -> str:
    slug = SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
    return slug[:80] or "untitled"
