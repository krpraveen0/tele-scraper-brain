from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceRecommendation:
    source_title: str
    total: int
    valuable: int
    sent: int
    avg_score: float
    max_score: float
    signal_ratio: float
    action: str
    reason: str
    suggested_min_save_score: float | None = None


def recommend_sources(rows: list[dict[str, Any]], min_samples: int = 10) -> list[SourceRecommendation]:
    recommendations = [_recommend_one(row, min_samples=min_samples) for row in rows]
    return sorted(recommendations, key=_sort_key)


def _recommend_one(row: dict[str, Any], min_samples: int) -> SourceRecommendation:
    source_title = str(row.get("source_title") or "Unknown")
    total = int(row.get("total") or 0)
    valuable = int(row.get("valuable") or 0)
    sent = int(row.get("sent") or 0)
    avg_score = float(row.get("avg_score") or 0.0)
    max_score = float(row.get("max_score") or 0.0)
    signal_ratio = (valuable / total * 100.0) if total else 0.0

    if total < min_samples:
        return SourceRecommendation(
            source_title=source_title,
            total=total,
            valuable=valuable,
            sent=sent,
            avg_score=avg_score,
            max_score=max_score,
            signal_ratio=signal_ratio,
            action="needs_more_data",
            reason=f"Only {total} sampled messages; collect at least {min_samples} before tuning.",
        )

    if valuable == 0 and max_score < 6.0:
        return SourceRecommendation(
            source_title=source_title,
            total=total,
            valuable=valuable,
            sent=sent,
            avg_score=avg_score,
            max_score=max_score,
            signal_ratio=signal_ratio,
            action="disable",
            reason="No useful signals found and max score is low.",
            suggested_min_save_score=9.0,
        )

    if signal_ratio < 5.0:
        return SourceRecommendation(
            source_title=source_title,
            total=total,
            valuable=valuable,
            sent=sent,
            avg_score=avg_score,
            max_score=max_score,
            signal_ratio=signal_ratio,
            action="raise_threshold_or_disable",
            reason="Very low signal ratio; source is likely noisy for your goals.",
            suggested_min_save_score=9.0,
        )

    if signal_ratio < 15.0:
        return SourceRecommendation(
            source_title=source_title,
            total=total,
            valuable=valuable,
            sent=sent,
            avg_score=avg_score,
            max_score=max_score,
            signal_ratio=signal_ratio,
            action="raise_threshold",
            reason="Low signal ratio; keep only very strong posts.",
            suggested_min_save_score=8.5,
        )

    if signal_ratio >= 40.0 and avg_score >= 7.0:
        return SourceRecommendation(
            source_title=source_title,
            total=total,
            valuable=valuable,
            sent=sent,
            avg_score=avg_score,
            max_score=max_score,
            signal_ratio=signal_ratio,
            action="keep_high_value",
            reason="High signal ratio and strong average score.",
            suggested_min_save_score=7.0,
        )

    if signal_ratio >= 25.0 and avg_score >= 6.5:
        return SourceRecommendation(
            source_title=source_title,
            total=total,
            valuable=valuable,
            sent=sent,
            avg_score=avg_score,
            max_score=max_score,
            signal_ratio=signal_ratio,
            action="keep",
            reason="Good enough signal ratio; keep monitoring.",
            suggested_min_save_score=7.5,
        )

    return SourceRecommendation(
        source_title=source_title,
        total=total,
        valuable=valuable,
        sent=sent,
        avg_score=avg_score,
        max_score=max_score,
        signal_ratio=signal_ratio,
        action="keep_testing",
        reason="Mixed signal quality; collect more data before changing config.",
    )


def _sort_key(item: SourceRecommendation) -> tuple[int, float, str]:
    priority = {
        "disable": 0,
        "raise_threshold_or_disable": 1,
        "raise_threshold": 2,
        "needs_more_data": 3,
        "keep_testing": 4,
        "keep": 5,
        "keep_high_value": 6,
    }.get(item.action, 9)
    return (priority, -item.signal_ratio, item.source_title.lower())
