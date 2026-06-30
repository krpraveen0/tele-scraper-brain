from __future__ import annotations

import re
from pathlib import Path

from app.models import StoredAsset


SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def export_asset_to_markdown(asset: StoredAsset, export_dir: Path) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"asset-{asset.id}-signal-{asset.signal_id}-{asset.asset_type}-{_slugify(asset.title)}.md"
    path = export_dir / filename
    path.write_text(_asset_markdown(asset), encoding="utf-8")
    return path


def _slugify(value: str) -> str:
    slug = SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
    return slug[:80] or "untitled"


def _asset_markdown(asset: StoredAsset) -> str:
    metadata = f"""---
asset_id: {asset.id}
signal_id: {asset.signal_id}
asset_type: {asset.asset_type}
rewritten: {str(asset.rewritten).lower()}
created_at: {asset.created_at}
---
""".strip()
    return f"{metadata}\n\n{asset.render()}\n"
