from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.models import StoredSignal
from app.storage import SignalStore


def build_daily_briefing(store: SignalStore, hours: int = 24, limit: int = 30) -> str:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    signals = store.saved_since(since, limit=limit)

    if not signals:
        return "Good morning Praveen 👋\n\nNo high-value signals were saved in the selected window."

    by_category: dict[str, list[StoredSignal]] = defaultdict(list)
    for signal in signals:
        by_category[signal.analysis.category].append(signal)

    sections = ["Good morning Praveen 👋", "", "Today’s Personal AI Briefing", ""]

    preferred_order = [
        "Career",
        "AI Engineering",
        "Research",
        "Teaching",
        "Content",
        "English",
        "Tools",
        "Global Economy",
        "Other",
    ]

    for category in preferred_order:
        category_signals = by_category.get(category, [])
        if not category_signals:
            continue

        sections.append(f"## {category}")
        for idx, signal in enumerate(category_signals[:3], start=1):
            analysis = signal.analysis
            link = f"\n   Link: {signal.permalink}" if signal.permalink else ""
            sections.append(
                f"{idx}. {analysis.summary}\n"
                f"   Score: {analysis.score}/10 | Action: {analysis.suggested_action}\n"
                f"   Why: {analysis.reason}{link}"
            )
        sections.append("")

    top = max(signals, key=lambda item: item.analysis.score)
    sections.extend(
        [
            "## One Priority Today",
            f"{top.analysis.suggested_action}: {top.analysis.summary}",
            "",
            "Generated locally by Praveen Signal OS.",
        ]
    )

    return "\n".join(sections).strip()
