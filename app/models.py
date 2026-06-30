from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from typing import Any


ALLOWED_CATEGORIES = {
    "Career",
    "AI Engineering",
    "Teaching",
    "Content",
    "English",
    "Research",
    "Tools",
    "Global Economy",
    "Other",
}

ALLOWED_ACTIONS = {
    "Read today",
    "Read weekend",
    "Apply",
    "Prepare resume",
    "Create LinkedIn post",
    "Create Medium outline",
    "Use in class",
    "Create diagram",
    "Practice speaking",
    "Try tool",
    "Archive",
    "Ignore",
}

ALLOWED_FEEDBACK_LABELS = {
    "useful",
    "not_useful",
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
    "archive",
}


def _clamp_score(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(10.0, number))


def _normalize_category(value: Any) -> str:
    cleaned = str(value or "Other").strip()
    return cleaned if cleaned in ALLOWED_CATEGORIES else "Other"


def _normalize_action(value: Any) -> str:
    cleaned = str(value or "Archive").strip()
    return cleaned if cleaned in ALLOWED_ACTIONS else "Archive"


def normalize_feedback_label(value: str) -> str:
    cleaned = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if cleaned not in ALLOWED_FEEDBACK_LABELS:
        allowed = ", ".join(sorted(ALLOWED_FEEDBACK_LABELS))
        raise ValueError(f"Unsupported feedback label '{value}'. Allowed labels: {allowed}")
    return cleaned


def _normalize_tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    tags: list[str] = []
    for tag in value:
        text = str(tag).strip().replace(" ", "")
        if not text:
            continue
        if not text.startswith("#"):
            text = f"#{text}"
        tags.append(text.lower())
    return tags[:8]


@dataclass(frozen=True)
class SignalAnalysis:
    is_valuable: bool = False
    score: float = 0.0
    category: str = "Other"
    reason: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    suggested_action: str = "Archive"
    career_relevance: float = 0.0
    ai_engineering_relevance: float = 0.0
    teaching_usefulness: float = 0.0
    content_potential: float = 0.0
    english_usefulness: float = 0.0
    research_depth: float = 0.0
    urgency: float = 0.0
    noise_risk: float = 0.0

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SignalAnalysis":
        return cls(
            is_valuable=bool(payload.get("is_valuable", False)),
            score=_clamp_score(payload.get("score")),
            category=_normalize_category(payload.get("category")),
            reason=str(payload.get("reason", "") or "").strip(),
            summary=str(payload.get("summary", "") or "").strip(),
            tags=_normalize_tags(payload.get("tags", [])),
            suggested_action=_normalize_action(payload.get("suggested_action")),
            career_relevance=_clamp_score(payload.get("career_relevance")),
            ai_engineering_relevance=_clamp_score(payload.get("ai_engineering_relevance")),
            teaching_usefulness=_clamp_score(payload.get("teaching_usefulness")),
            content_potential=_clamp_score(payload.get("content_potential")),
            english_usefulness=_clamp_score(payload.get("english_usefulness")),
            research_depth=_clamp_score(payload.get("research_depth")),
            urgency=_clamp_score(payload.get("urgency")),
            noise_risk=_clamp_score(payload.get("noise_risk")),
        )

    @classmethod
    def safe_default(cls, reason: str) -> "SignalAnalysis":
        return cls(
            is_valuable=False,
            score=0.0,
            category="Other",
            reason=reason,
            summary="Could not reliably analyze this message.",
            tags=["#unprocessed"],
            suggested_action="Archive",
            noise_risk=10.0,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "SignalAnalysis":
        return cls.from_payload(json.loads(value))


@dataclass(frozen=True)
class TelegramSignal:
    source_id: str
    source_title: str
    message_id: int
    message_text: str
    message_date: datetime
    permalink: str | None = None
    source_ref: str | None = None

    @property
    def dedupe_key(self) -> str:
        return f"{self.source_id}:{self.message_id}"


@dataclass(frozen=True)
class StoredSignal:
    id: int
    source_id: str
    source_title: str
    message_id: int
    message_text: str
    message_date: str
    permalink: str | None
    analysis: SignalAnalysis
    saved_to_telegram: bool
    created_at: str


@dataclass(frozen=True)
class FeedbackEntry:
    id: int
    signal_id: int
    label: str
    notes: str
    created_at: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_analysis(payload: dict[str, Any]) -> SignalAnalysis:
    try:
        return SignalAnalysis.from_payload(payload)
    except Exception as exc:  # noqa: BLE001 - keep pipeline resilient to malformed LLM output.
        return SignalAnalysis.safe_default(f"Invalid LLM JSON schema: {exc}")
