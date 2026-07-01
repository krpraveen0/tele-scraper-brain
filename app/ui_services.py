from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.asset_exporter import export_asset_to_markdown
from app.asset_generator import ALLOWED_ASSET_TYPES, GeneratedAsset, generate_asset
from app.asset_rewriter import create_asset_rewriter
from app.config import Settings
from app.daily_action_brief import build_daily_action_brief
from app.feedback_profile import build_feedback_profile
from app.idea_lab import IdeaLabReport, generate_idea_lab_report
from app.models import ALLOWED_FEEDBACK_LABELS, StoredAsset, StoredSignal
from app.storage import SignalStore


@dataclass(frozen=True)
class DashboardSnapshot:
    total_signals: int
    valuable_signals: int
    unsent_signals: int
    recent_assets: int
    feedback_labels: int
    top_categories: list[tuple[str, int]]
    top_sources: list[tuple[str, int]]


@dataclass(frozen=True)
class AssetResult:
    asset: GeneratedAsset
    stored_asset: StoredAsset | None
    exported_path: Path | None
    rewritten: bool


def dashboard_snapshot(store: SignalStore) -> DashboardSnapshot:
    signals = list(store.iter_all())
    unsent = store.unsent_saved(limit=500)
    assets = store.recent_assets(limit=500)
    feedback = store.recent_feedback(limit=1000)

    category_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    valuable = 0
    for signal in signals:
        if signal.analysis.is_valuable:
            valuable += 1
        category_counts[signal.analysis.category] = category_counts.get(signal.analysis.category, 0) + 1
        source_counts[signal.source_title] = source_counts.get(signal.source_title, 0) + 1

    return DashboardSnapshot(
        total_signals=len(signals),
        valuable_signals=valuable,
        unsent_signals=len(unsent),
        recent_assets=len(assets),
        feedback_labels=len(feedback),
        top_categories=sorted(category_counts.items(), key=lambda item: item[1], reverse=True)[:8],
        top_sources=sorted(source_counts.items(), key=lambda item: item[1], reverse=True)[:8],
    )


def list_signals(store: SignalStore, view: str, limit: int) -> list[StoredSignal]:
    normalized_view = view.strip().lower()
    if normalized_view == "unsent":
        return store.unsent_saved(limit=limit)
    if normalized_view == "recent sent":
        return store.recent_saved(limit=limit)
    return list(store.iter_all())[:limit]


def signal_table_rows(signals: list[StoredSignal]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for signal in signals:
        rows.append(
            {
                "id": signal.id,
                "score": signal.analysis.score,
                "category": signal.analysis.category,
                "action": signal.analysis.suggested_action,
                "source": signal.source_title,
                "summary": signal.analysis.summary or signal.analysis.reason or signal.message_text[:140],
                "sent": signal.saved_to_telegram,
                "created_at": signal.created_at,
            }
        )
    return rows


def add_feedback_label(store: SignalStore, signal_id: int, label: str, notes: str = "") -> str:
    feedback = store.add_feedback(signal_id=signal_id, label=label, notes=notes)
    return f"Saved feedback #{feedback.id}: {feedback.label} for signal {feedback.signal_id}"


def create_idea_lab_report(store: SignalStore, signal_id: int) -> IdeaLabReport:
    signal = store.get_signal(signal_id)
    if signal is None:
        raise ValueError(f"Signal id {signal_id} does not exist.")
    return generate_idea_lab_report(signal)


def create_asset_result(
    settings: Settings,
    store: SignalStore,
    signal_id: int,
    asset_type: str,
    rewrite: bool = False,
    save: bool = False,
    export: bool = False,
    export_dir: str | None = None,
) -> AssetResult:
    signal = store.get_signal(signal_id)
    if signal is None:
        raise ValueError(f"Signal id {signal_id} does not exist.")

    asset = generate_asset(signal, asset_type)
    rewritten = False
    if rewrite:
        rewriter = create_asset_rewriter(settings)
        asset = rewriter.rewrite(signal, asset)
        rewritten = True

    stored_asset: StoredAsset | None = None
    exported_path: Path | None = None
    if save or export:
        stored_asset = store.save_asset(asset, rewritten=rewritten)

    if export:
        if stored_asset is None:
            stored_asset = store.save_asset(asset, rewritten=rewritten)
        target_dir = Path(export_dir) if export_dir else settings.asset_export_dir
        exported_path = export_asset_to_markdown(stored_asset, target_dir)
        store.mark_asset_exported(stored_asset.id, exported_path)
        stored_asset = store.get_asset(stored_asset.id) or stored_asset

    return AssetResult(asset=asset, stored_asset=stored_asset, exported_path=exported_path, rewritten=rewritten)


def build_action_brief(store: SignalStore, hours: int = 24, limit: int = 60) -> str:
    return build_daily_action_brief(store, hours=hours, limit=limit)


def build_profile(store: SignalStore, limit: int = 200) -> str:
    return build_feedback_profile(store, limit=limit)


def allowed_feedback_labels() -> list[str]:
    return sorted(ALLOWED_FEEDBACK_LABELS)


def allowed_asset_types() -> list[str]:
    return sorted(ALLOWED_ASSET_TYPES)
