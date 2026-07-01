from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.asset_generator import ALLOWED_ASSET_TYPES
from app.models import SignalAnalysis, TelegramSignal
from app.storage import SignalStore
from app.ui_services import (
    add_feedback_label,
    allowed_asset_types,
    allowed_feedback_labels,
    create_asset_result,
    create_idea_lab_report,
    dashboard_snapshot,
    list_signals,
    signal_table_rows,
)


class DummySettings:
    asset_export_dir = Path("assets")


def save_signal(store: SignalStore, message_id: int, category: str = "AI Engineering", saved: bool = False) -> int:
    return store.save(
        TelegramSignal(
            source_id=f"source-{message_id}",
            source_title=f"Source {message_id}",
            message_id=message_id,
            message_text=f"Useful signal {message_id}",
            message_date=datetime.now(timezone.utc),
            permalink=f"https://t.me/test/{message_id}",
        ),
        SignalAnalysis(
            is_valuable=True,
            score=8.0,
            category=category,
            summary=f"Summary {message_id}",
            tags=["#test"],
            suggested_action="Read today",
        ),
        saved_to_telegram=saved,
    )


def test_dashboard_snapshot_counts_signals_assets_and_feedback(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_signal(store, 1, category="Career")
    add_feedback_label(store, signal_id, "useful")
    result = create_asset_result(DummySettings(), store, signal_id, "linkedin", save=True)

    snapshot = dashboard_snapshot(store)

    assert snapshot.total_signals == 1
    assert snapshot.valuable_signals == 1
    assert snapshot.unsent_signals == 1
    assert snapshot.feedback_labels == 1
    assert snapshot.recent_assets == 1
    assert snapshot.top_categories == [("Career", 1)]
    assert result.stored_asset is not None


def test_list_signals_views_and_rows(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    unsent_id = save_signal(store, 1, saved=False)
    sent_id = save_signal(store, 2, saved=True)

    unsent = list_signals(store, "Unsent", limit=10)
    sent = list_signals(store, "Recent sent", limit=10)
    all_rows = signal_table_rows(list_signals(store, "All", limit=10))

    assert [item.id for item in unsent] == [unsent_id]
    assert [item.id for item in sent] == [sent_id]
    assert {row["id"] for row in all_rows} == {unsent_id, sent_id}


def test_create_asset_result_can_export(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_signal(store, 1)

    result = create_asset_result(
        DummySettings(),
        store,
        signal_id,
        "teaching_example",
        save=True,
        export=True,
        export_dir=str(tmp_path / "exports"),
    )

    assert result.stored_asset is not None
    assert result.exported_path is not None
    assert result.exported_path.exists()
    assert result.asset.asset_type == "teaching_example"


def test_create_idea_lab_report_from_saved_signal(tmp_path: Path) -> None:
    store = SignalStore(tmp_path / "signals.db")
    signal_id = save_signal(store, 1)

    report = create_idea_lab_report(store, signal_id)

    assert report.signal_id == signal_id
    assert report.source == "Source 1"
    assert len(report.content_angles) == 10
    assert "# Idea Lab Report" in report.render()


def test_allowed_ui_options_are_exposed() -> None:
    assert "useful" in allowed_feedback_labels()
    assert sorted(ALLOWED_ASSET_TYPES) == allowed_asset_types()
