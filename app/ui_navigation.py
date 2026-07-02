from __future__ import annotations


TOP_LEVEL_TABS = [
    "Dashboard",
    "Signals Inbox",
    "Creator Workspace",
    "Assets",
    "Briefings & Feedback",
]

CREATOR_WORKSPACE_TABS = [
    "Ideas & Blueprints",
    "Quality Gate",
    "Publishing Queue",
    "Export & Archive",
]

ASSET_WORKSPACE_TABS = [
    "Generate Asset",
    "Asset History",
]

BRIEFING_FEEDBACK_TABS = [
    "Daily Brief",
    "Feedback Profile",
]


def navigation_summary() -> list[dict[str, object]]:
    return [
        {"section": "Dashboard", "children": [], "description": "Health, counts, and next actions."},
        {"section": "Signals Inbox", "children": [], "description": "Review signals, feedback, and quick assets."},
        {"section": "Creator Workspace", "children": CREATOR_WORKSPACE_TABS, "description": "Create, check, queue, export, and archive creator work."},
        {"section": "Assets", "children": ASSET_WORKSPACE_TABS, "description": "Generate and review reusable assets."},
        {"section": "Briefings & Feedback", "children": BRIEFING_FEEDBACK_TABS, "description": "Generate briefs and inspect feedback intelligence."},
    ]
