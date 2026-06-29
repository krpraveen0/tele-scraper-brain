from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


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


class SignalAnalysis(BaseModel):
    is_valuable: bool = False
    score: float = Field(default=0.0, ge=0.0, le=10.0)
    category: str = "Other"
    reason: str = ""
    summary: str = ""
    tags: list[str] = Field(default_factory=list)
    suggested_action: str = "Archive"
    career_relevance: float = Field(default=0.0, ge=0.0, le=10.0)
    ai_engineering_relevance: float = Field(default=0.0, ge=0.0, le=10.0)
    teaching_usefulness: float = Field(default=0.0, ge=0.0, le=10.0)
    content_potential: float = Field(default=0.0, ge=0.0, le=10.0)
    english_usefulness: float = Field(default=0.0, ge=0.0, le=10.0)
    research_depth: float = Field(default=0.0, ge=0.0, le=10.0)
    urgency: float = Field(default=0.0, ge=0.0, le=10.0)
    noise_risk: float = Field(default=0.0, ge=0.0, le=10.0)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        cleaned = (value or "Other").strip()
        return cleaned if cleaned in ALLOWED_CATEGORIES else "Other"

    @field_validator("suggested_action")
    @classmethod
    def normalize_action(cls, value: str) -> str:
        cleaned = (value or "Archive").strip()
        return cleaned if cleaned in ALLOWED_ACTIONS else "Archive"

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        tags = []
        for tag in value or []:
            text = str(tag).strip().replace(" ", "")
            if not text:
                continue
            if not text.startswith("#"):
                text = f"#{text}"
            tags.append(text.lower())
        return tags[:8]

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


@dataclass(frozen=True)
class TelegramSignal:
    source_id: str
    source_title: str
    message_id: int
    message_text: str
    message_date: datetime
    permalink: str | None = None

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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_analysis(payload: dict[str, Any]) -> SignalAnalysis:
    try:
        return SignalAnalysis.model_validate(payload)
    except ValidationError as exc:
        return SignalAnalysis.safe_default(f"Invalid LLM JSON schema: {exc.errors()[:2]}")
