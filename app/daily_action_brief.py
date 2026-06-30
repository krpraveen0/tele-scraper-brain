from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.models import StoredAsset, StoredSignal
from app.storage import SignalStore


@dataclass(frozen=True)
class ActionSlot:
    title: str
    categories: tuple[str, ...]
    fallback_action: str
    prompt: str


ACTION_SLOTS = (
    ActionSlot(
        title="Career move",
        categories=("Career",),
        fallback_action="Prepare one career improvement step.",
        prompt="Use this to update resume keywords, prepare one interview answer, or shortlist one opportunity.",
    ),
    ActionSlot(
        title="AI engineering learning",
        categories=("AI Engineering", "Research", "Tools"),
        fallback_action="Study one practical AI engineering concept.",
        prompt="Use this to learn or test one production AI pattern.",
    ),
    ActionSlot(
        title="Teaching idea",
        categories=("Teaching",),
        fallback_action="Create one class example or mini exercise.",
        prompt="Use this to prepare a practical teaching example for students.",
    ),
    ActionSlot(
        title="Content idea",
        categories=("Content", "AI Engineering", "Research"),
        fallback_action="Draft one LinkedIn or Medium idea.",
        prompt="Use this to draft a human-sounding LinkedIn post or Medium outline.",
    ),
    ActionSlot(
        title="English practice",
        categories=("English", "Career"),
        fallback_action="Practice one leadership sentence aloud.",
        prompt="Use this to practice a 30-second workplace explanation.",
    ),
    ActionSlot(
        title="Economy awareness",
        categories=("Global Economy",),
        fallback_action="Review one economy signal and connect it to career or investing awareness.",
        prompt="Use this to understand one global or India market signal.",
    ),
)


def build_daily_action_brief(store: SignalStore, hours: int = 24, limit: int = 60) -> str:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    signals = store.saved_since(since, limit=limit)
    assets = store.recent_assets(limit=5)
    feedback = store.feedback_summary()

    if not signals:
        return _empty_brief(hours=hours, assets=assets, feedback=feedback)

    by_category: dict[str, list[StoredSignal]] = defaultdict(list)
    for signal in sorted(signals, key=lambda item: item.analysis.score, reverse=True):
        by_category[signal.analysis.category].append(signal)

    used_signal_ids: set[int] = set()
    lines = ["Good morning Praveen 👋", "", "# Daily Action Brief", "", f"Window: last {hours} hours", ""]

    for index, slot in enumerate(ACTION_SLOTS, start=1):
        signal = _pick_signal(slot.categories, by_category, used_signal_ids)
        lines.extend(_render_slot(index, slot, signal))
        if signal:
            used_signal_ids.add(signal.id)

    lines.extend(_render_asset_section(assets))
    lines.extend(_render_feedback_section(feedback))
    lines.extend(_render_next_command_hint())
    return "\n".join(lines).strip()


def _pick_signal(
    categories: tuple[str, ...],
    by_category: dict[str, list[StoredSignal]],
    used_signal_ids: set[int],
) -> StoredSignal | None:
    for category in categories:
        for signal in by_category.get(category, []):
            if signal.id not in used_signal_ids:
                return signal
    return None


def _render_slot(index: int, slot: ActionSlot, signal: StoredSignal | None) -> list[str]:
    if signal is None:
        return [
            f"## {index}. {slot.title}",
            f"Action: {slot.fallback_action}",
            "Signal: No matching saved signal in this window.",
            "",
        ]

    analysis = signal.analysis
    link = f"\nLink: {signal.permalink}" if signal.permalink else ""
    return [
        f"## {index}. {slot.title}",
        f"Action: {analysis.suggested_action}",
        f"Signal ID: {signal.id}",
        f"Source: {signal.source_title}",
        f"Summary: {analysis.summary or analysis.reason}",
        f"Why this matters: {slot.prompt}",
        f"Score: {analysis.score}/10 | Category: {analysis.category}{link}",
        "",
    ]


def _render_asset_section(assets: list[StoredAsset]) -> list[str]:
    lines = ["## Asset follow-up"]
    if not assets:
        lines.extend([
            "No generated assets yet.",
            "Suggested command: python -m app.main create-asset --id <signal_id> --type linkedin --save --export",
            "",
        ])
        return lines

    for asset in assets[:3]:
        export_note = f" | Export: {asset.exported_path}" if asset.exported_path else ""
        lines.append(
            f"- Asset {asset.id}: {asset.asset_type} from signal {asset.signal_id} | Sent: {'yes' if asset.sent_to_telegram else 'no'}{export_note}"
        )
    lines.append("")
    return lines


def _render_feedback_section(feedback: list[dict[str, object]]) -> list[str]:
    lines = ["## Feedback snapshot"]
    if not feedback:
        lines.extend([
            "No feedback labels yet.",
            "Suggested command: python -m app.main feedback --id <signal_id> --label useful",
            "",
        ])
        return lines

    top = feedback[:5]
    for row in top:
        lines.append(f"- {row['label']}: {row['count']} item(s), avg score {float(row['avg_score'] or 0.0):.1f}")
    lines.append("")
    return lines


def _render_next_command_hint() -> list[str]:
    return [
        "## Suggested next commands",
        "python -m app.main unsent --limit 20",
        "python -m app.main recommend-sources",
        "python -m app.main assets --limit 20",
        "",
        "Generated locally by Praveen Signal OS.",
    ]


def _empty_brief(hours: int, assets: list[StoredAsset], feedback: list[dict[str, object]]) -> str:
    lines = [
        "Good morning Praveen 👋",
        "",
        "# Daily Action Brief",
        "",
        f"No high-value saved signals were found in the last {hours} hours.",
        "",
        "Suggested recovery flow:",
        "1. Run: python -m app.main backfill --limit 20",
        "2. Review: python -m app.main unsent --limit 20",
        "3. Tune: python -m app.main recommend-sources",
        "",
    ]
    lines.extend(_render_asset_section(assets))
    lines.extend(_render_feedback_section(feedback))
    lines.append("Generated locally by Praveen Signal OS.")
    return "\n".join(lines).strip()
