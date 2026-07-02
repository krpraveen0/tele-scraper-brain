from __future__ import annotations

from app.ui_navigation import (
    ASSET_WORKSPACE_TABS,
    BRIEFING_FEEDBACK_TABS,
    CREATOR_WORKSPACE_TABS,
    TOP_LEVEL_TABS,
    navigation_summary,
)


def test_top_level_tabs_are_simplified() -> None:
    assert TOP_LEVEL_TABS == [
        "Dashboard",
        "Source Intake",
        "Signals Inbox",
        "Creator Workspace",
        "Assets",
        "Briefings & Feedback",
    ]
    assert len(TOP_LEVEL_TABS) == 6


def test_creator_workspace_keeps_creator_flows() -> None:
    assert CREATOR_WORKSPACE_TABS == [
        "Ideas & Blueprints",
        "Quality Gate",
        "Publishing Queue",
        "Export & Archive",
    ]


def test_assets_and_feedback_are_grouped() -> None:
    assert ASSET_WORKSPACE_TABS == ["Generate Asset", "Asset History"]
    assert BRIEFING_FEEDBACK_TABS == ["Daily Brief", "Feedback Profile"]


def test_navigation_summary_is_dashboard_friendly() -> None:
    summary = navigation_summary()

    assert len(summary) == len(TOP_LEVEL_TABS)
    assert [item["section"] for item in summary] == TOP_LEVEL_TABS
    assert all("description" in item for item in summary)
    assert any(item["section"] == "Source Intake" for item in summary)
