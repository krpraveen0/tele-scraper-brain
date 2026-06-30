from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.models import SignalAnalysis, TelegramSignal


CATEGORY_DESTINATION_KEYS = {
    "Career": "career",
    "AI Engineering": "ai_engineering",
    "Teaching": "teaching",
    "Content": "content",
    "English": "english",
    "Research": "research",
    "Tools": "tools",
    "Global Economy": "global_economy",
    "Other": "default",
}


def normalize_key(value: str | None) -> str:
    return (value or "").strip().lower().replace("@", "")


def normalize_destination_key(value: str | None) -> str:
    return (value or "default").strip().lower().replace(" ", "_").replace("-", "_") or "default"


@dataclass(frozen=True)
class SourceConfig:
    name: str
    handle: str
    enabled: bool = True
    trust_score: float = 5.0
    category_hint: str = "Other"
    min_save_score: float | None = None
    destination: str = "default"
    notes: str = ""

    @property
    def normalized_handle(self) -> str:
        return normalize_key(self.handle)

    @property
    def normalized_name(self) -> str:
        return normalize_key(self.name)

    @property
    def chat_ref(self) -> str:
        return self.handle or self.name


class SourceRegistry:
    def __init__(self, sources: list[SourceConfig]) -> None:
        self.sources = sources
        self._by_key: dict[str, SourceConfig] = {}
        for source in sources:
            for key in {source.normalized_handle, source.normalized_name}:
                if key:
                    self._by_key[key] = source

    @classmethod
    def empty(cls) -> "SourceRegistry":
        return cls([])

    @classmethod
    def from_yaml(cls, path: Path) -> "SourceRegistry":
        if not path.exists():
            return cls.empty()

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        raw_sources = data.get("sources", [])
        if not isinstance(raw_sources, list):
            raise RuntimeError(f"{path} must contain a top-level 'sources' list.")

        sources: list[SourceConfig] = []
        for index, item in enumerate(raw_sources, start=1):
            if not isinstance(item, dict):
                raise RuntimeError(f"Source entry #{index} in {path} must be a mapping.")
            handle = str(item.get("handle", "") or "").strip()
            name = str(item.get("name", "") or handle or f"Source {index}").strip()
            if not handle and not name:
                raise RuntimeError(f"Source entry #{index} in {path} must include a name or handle.")
            sources.append(
                SourceConfig(
                    name=name,
                    handle=handle,
                    enabled=bool(item.get("enabled", True)),
                    trust_score=_clamp(item.get("trust_score", 5.0)),
                    category_hint=str(item.get("category_hint", "Other") or "Other").strip(),
                    min_save_score=_optional_float(item.get("min_save_score")),
                    destination=normalize_destination_key(str(item.get("destination", "default") or "default")),
                    notes=str(item.get("notes", "") or "").strip(),
                )
            )
        return cls(sources)

    @classmethod
    def from_legacy_chats(cls, chats: list[str], default_min_save_score: float) -> "SourceRegistry":
        return cls(
            [
                SourceConfig(
                    name=chat,
                    handle=chat,
                    enabled=True,
                    trust_score=5.0,
                    category_hint="Other",
                    min_save_score=default_min_save_score,
                    destination="default",
                )
                for chat in chats
            ]
        )

    def enabled_sources(self) -> list[SourceConfig]:
        return [source for source in self.sources if source.enabled]

    def enabled_chat_refs(self) -> list[str]:
        return [source.chat_ref for source in self.enabled_sources() if source.chat_ref]

    def find_for_signal(self, signal: TelegramSignal) -> SourceConfig | None:
        candidates = [
            getattr(signal, "source_ref", None),
            signal.source_title,
            signal.source_id,
        ]
        if signal.permalink and "t.me/" in signal.permalink:
            parts = signal.permalink.split("t.me/", 1)[-1].split("/", 1)
            if parts:
                candidates.append(parts[0])

        for candidate in candidates:
            source = self._by_key.get(normalize_key(candidate))
            if source:
                return source
        return None

    def min_score_for(self, signal: TelegramSignal, default_min_score: float) -> float:
        source = self.find_for_signal(signal)
        if source and source.min_save_score is not None:
            return source.min_save_score
        return default_min_score

    def destination_key_for(self, signal: TelegramSignal, analysis: SignalAnalysis) -> str:
        source = self.find_for_signal(signal)
        if source and source.destination != "default":
            return source.destination
        return CATEGORY_DESTINATION_KEYS.get(analysis.category, "default")

    def destination_chat_for(
        self,
        signal: TelegramSignal,
        analysis: SignalAnalysis,
        destinations: dict[str, str],
        default_chat: str,
    ) -> str:
        destination_key = self.destination_key_for(signal, analysis)
        return destinations.get(destination_key) or destinations.get("default") or default_chat


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return _clamp(value)


def _clamp(value: Any, default: float = 5.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(10.0, number))
