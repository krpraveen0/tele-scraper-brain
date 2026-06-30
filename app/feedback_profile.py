from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from app.models import FeedbackEntry, StoredAsset, StoredSignal
from app.storage import SignalStore


POSITIVE_LABELS = {
    "useful",
    "linkedin_idea",
    "medium_idea",
    "teaching_example",
    "career_opportunity",
    "research_note",
    "tool_to_try",
    "english_practice",
    "economy_signal",
    "read_today",
    "read_weekend",
}

NEGATIVE_LABELS = {"not_useful", "archive"}


@dataclass(frozen=True)
class FeedbackSignal:
    signal: StoredSignal
    feedback: list[FeedbackEntry]
    assets: list[StoredAsset]

    @property
    def positive_count(self) -> int:
        return sum(1 for item in self.feedback if item.label in POSITIVE_LABELS)

    @property
    def negative_count(self) -> int:
        return sum(1 for item in self.feedback if item.label in NEGATIVE_LABELS)

    @property
    def useful_score(self) -> int:
        return self.positive_count - self.negative_count


@dataclass(frozen=True)
class ProfileSection:
    title: str
    rows: list[str]


def build_feedback_profile(store: SignalStore, limit: int = 200) -> str:
    records = _load_feedback_records(store, limit=limit)
    assets = store.recent_assets(limit=limit)

    if not records:
        return _empty_profile(assets)

    sections = [
        _summary_section(records, assets),
        _liked_patterns_section(records),
        _ignored_patterns_section(records),
        _source_section(records),
        _tag_section(records),
        _asset_section(records, assets),
        _tuning_section(records),
    ]

    lines = ["# Feedback Intelligence Profile", "", "This profile is generated from your local feedback labels.", ""]
    for section in sections:
        lines.append(f"## {section.title}")
        lines.extend(section.rows)
        lines.append("")
    lines.append("Generated locally by Praveen Signal OS.")
    return "\n".join(lines).strip()


def _load_feedback_records(store: SignalStore, limit: int) -> list[FeedbackSignal]:
    records: list[FeedbackSignal] = []
    for signal in list(store.iter_all())[:limit]:
        feedback = store.feedback_for_signal(signal.id)
        if not feedback:
            continue
        assets = [asset for asset in store.recent_assets(limit=limit) if asset.signal_id == signal.id]
        records.append(FeedbackSignal(signal=signal, feedback=feedback, assets=assets))
    return records


def _summary_section(records: list[FeedbackSignal], assets: list[StoredAsset]) -> ProfileSection:
    positive = sum(item.positive_count for item in records)
    negative = sum(item.negative_count for item in records)
    total_feedback = positive + negative
    useful_ratio = (positive / total_feedback * 100.0) if total_feedback else 0.0
    return ProfileSection(
        title="Snapshot",
        rows=[
            f"- Feedback-labelled signals: {len(records)}",
            f"- Positive labels: {positive}",
            f"- Negative labels: {negative}",
            f"- Useful ratio: {useful_ratio:.0f}%",
            f"- Generated assets in recent history: {len(assets)}",
        ],
    )


def _liked_patterns_section(records: list[FeedbackSignal]) -> ProfileSection:
    categories = Counter(record.signal.analysis.category for record in records if record.useful_score > 0)
    labels = Counter(label.label for record in records for label in record.feedback if label.label in POSITIVE_LABELS)
    rows = ["What you seem to like:"]
    rows.extend(_counter_rows(categories, "category"))
    rows.append("")
    rows.append("Positive labels you use most:")
    rows.extend(_counter_rows(labels, "label"))
    return ProfileSection(title="What Praveen likes", rows=rows)


def _ignored_patterns_section(records: list[FeedbackSignal]) -> ProfileSection:
    categories = Counter(record.signal.analysis.category for record in records if record.useful_score < 0)
    sources = Counter(record.signal.source_title for record in records if record.useful_score < 0)
    rows = ["What you seem to ignore or reject:"]
    rows.extend(_counter_rows(categories, "category"))
    rows.append("")
    rows.append("Noisy sources from your own labels:")
    rows.extend(_counter_rows(sources, "source"))
    return ProfileSection(title="What Praveen ignores", rows=rows)


def _source_section(records: list[FeedbackSignal]) -> ProfileSection:
    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "negative": 0, "signals": 0})
    for record in records:
        source = record.signal.source_title
        stats[source]["positive"] += record.positive_count
        stats[source]["negative"] += record.negative_count
        stats[source]["signals"] += 1

    ranked = sorted(
        stats.items(),
        key=lambda item: (item[1]["positive"] - item[1]["negative"], item[1]["signals"]),
        reverse=True,
    )
    rows = []
    for source, data in ranked[:8]:
        score = data["positive"] - data["negative"]
        rows.append(f"- {source}: score {score}, +{data['positive']} / -{data['negative']} across {data['signals']} signal(s)")
    if not rows:
        rows.append("- Not enough source feedback yet.")
    return ProfileSection(title="Source intelligence", rows=rows)


def _tag_section(records: list[FeedbackSignal]) -> ProfileSection:
    positive_tags: Counter[str] = Counter()
    negative_tags: Counter[str] = Counter()
    for record in records:
        target = positive_tags if record.useful_score >= 0 else negative_tags
        for tag in record.signal.analysis.tags:
            target[tag] += 1

    rows = ["Useful tags:"]
    rows.extend(_counter_rows(positive_tags, "tag"))
    rows.append("")
    rows.append("Tags to watch carefully:")
    rows.extend(_counter_rows(negative_tags, "tag"))
    return ProfileSection(title="Tag preferences", rows=rows)


def _asset_section(records: list[FeedbackSignal], assets: list[StoredAsset]) -> ProfileSection:
    asset_types = Counter(asset.asset_type for asset in assets)
    sent_count = sum(1 for asset in assets if asset.sent_to_telegram)
    exported_count = sum(1 for asset in assets if asset.exported_path)
    rows = [
        f"- Recent generated assets: {len(assets)}",
        f"- Sent to Telegram: {sent_count}",
        f"- Exported as Markdown: {exported_count}",
        "",
        "Asset types used most:",
    ]
    rows.extend(_counter_rows(asset_types, "asset"))

    labelled_asset_records = [record for record in records if record.assets]
    if labelled_asset_records:
        rows.append("")
        rows.append(f"Assets connected to labelled signals: {len(labelled_asset_records)}")
    return ProfileSection(title="Asset outcomes", rows=rows)


def _tuning_section(records: list[FeedbackSignal]) -> ProfileSection:
    rows = []
    positive_categories = Counter(record.signal.analysis.category for record in records if record.useful_score > 0)
    negative_categories = Counter(record.signal.analysis.category for record in records if record.useful_score < 0)

    for category, count in positive_categories.most_common(5):
        rows.append(f"- Boost signals in {category} when they are practical, source-linked, and action-oriented. Seen positive {count} time(s).")
    for category, count in negative_categories.most_common(5):
        rows.append(f"- Penalize generic {category} signals unless they contain concrete links, tools, roles, or examples. Seen negative {count} time(s).")

    if not rows:
        rows.append("- Collect at least 20 feedback labels before serious prompt tuning.")

    rows.extend(
        [
            "",
            "Suggested next step:",
            "- Use this profile to update the classification prompt and source thresholds after 30-50 feedback labels.",
        ]
    )
    return ProfileSection(title="Prompt and source tuning suggestions", rows=rows)


def _counter_rows(counter: Counter[str], item_name: str, limit: int = 6) -> list[str]:
    if not counter:
        return [f"- Not enough {item_name} data yet."]
    return [f"- {name}: {count}" for name, count in counter.most_common(limit)]


def _empty_profile(assets: list[StoredAsset]) -> str:
    lines = [
        "# Feedback Intelligence Profile",
        "",
        "No feedback-labelled signals found yet.",
        "",
        "Start collecting labels:",
        "1. python -m app.main unsent --limit 20",
        "2. python -m app.main feedback --id <signal_id> --label useful",
        "3. python -m app.main feedback --id <signal_id> --label not_useful --notes \"reason\"",
        "",
        f"Recent generated assets: {len(assets)}",
        "",
        "Generated locally by Praveen Signal OS.",
    ]
    return "\n".join(lines).strip()
