from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

from app.models import SignalAnalysis, TelegramSignal
from app.sources import SourceRegistry, normalize_destination_key


DESTINATION_ENV_KEYS = {
    "default": "DEST_DEFAULT_CHAT",
    "career": "DEST_CAREER_CHAT",
    "ai_engineering": "DEST_AI_ENGINEERING_CHAT",
    "teaching": "DEST_TEACHING_CHAT",
    "content": "DEST_CONTENT_CHAT",
    "english": "DEST_ENGLISH_CHAT",
    "research": "DEST_RESEARCH_CHAT",
    "tools": "DEST_TOOLS_CHAT",
    "global_economy": "DEST_GLOBAL_ECONOMY_CHAT",
    "other": "DEST_OTHER_CHAT",
}


@dataclass(frozen=True)
class Settings:
    tg_api_id: int
    tg_api_hash: str
    tg_phone: str
    source_chats: list[str]
    destination_chat: str
    briefing_chat: str
    destinations: dict[str, str]
    source_registry: SourceRegistry
    sources_config_path: Path
    llm_provider: str
    ollama_url: str
    ollama_model: str
    opencode_model: str
    opencode_attach_url: str
    opencode_timeout_seconds: int
    min_save_score: float
    max_message_chars: int
    database_path: Path
    telegram_session_name: str

    def min_save_score_for(self, signal: TelegramSignal) -> float:
        return self.source_registry.min_score_for(signal, self.min_save_score)

    def destination_for(self, signal: TelegramSignal, analysis: SignalAnalysis) -> str:
        return self.source_registry.destination_chat_for(signal, analysis, self.destinations, self.destination_chat)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_destinations(default_chat: str) -> dict[str, str]:
    destinations = {"default": os.getenv("DEST_DEFAULT_CHAT", "").strip() or default_chat}
    for key, env_key in DESTINATION_ENV_KEYS.items():
        value = os.getenv(env_key, "").strip()
        if value:
            destinations[normalize_destination_key(key)] = value
    return destinations


def load_settings() -> Settings:
    load_dotenv()

    legacy_source_chats = _split_csv(os.getenv("SOURCE_CHATS", ""))
    destination_chat = os.getenv("DESTINATION_CHAT", "").strip()
    briefing_chat = os.getenv("BRIEFING_CHAT", "").strip() or destination_chat
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    min_save_score = float(os.getenv("MIN_SAVE_SCORE", "7.0"))
    sources_config_path = Path(os.getenv("SOURCES_CONFIG_PATH", "sources.yaml"))

    if llm_provider not in {"ollama", "opencode"}:
        raise RuntimeError("LLM_PROVIDER must be either 'ollama' or 'opencode'.")

    source_registry = SourceRegistry.from_yaml(sources_config_path)
    if not source_registry.sources:
        source_registry = SourceRegistry.from_legacy_chats(legacy_source_chats, default_min_save_score=min_save_score)

    source_chats = source_registry.enabled_chat_refs()

    missing = []
    for key in ["TG_API_ID", "TG_API_HASH", "TG_PHONE", "DESTINATION_CHAT"]:
        if not os.getenv(key):
            missing.append(key)
    if not source_chats:
        missing.append("SOURCE_CHATS or sources.yaml")

    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required environment values: {joined}. Copy .env.example to .env and fill it.")

    return Settings(
        tg_api_id=int(os.environ["TG_API_ID"]),
        tg_api_hash=os.environ["TG_API_HASH"].strip(),
        tg_phone=os.environ["TG_PHONE"].strip(),
        source_chats=source_chats,
        destination_chat=destination_chat,
        briefing_chat=briefing_chat,
        destinations=_load_destinations(destination_chat),
        source_registry=source_registry,
        sources_config_path=sources_config_path,
        llm_provider=llm_provider,
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip(),
        opencode_model=os.getenv("OPENCODE_MODEL", "").strip(),
        opencode_attach_url=os.getenv("OPENCODE_ATTACH_URL", "").strip(),
        opencode_timeout_seconds=int(os.getenv("OPENCODE_TIMEOUT_SECONDS", "180")),
        min_save_score=min_save_score,
        max_message_chars=int(os.getenv("MAX_MESSAGE_CHARS", "5000")),
        database_path=Path(os.getenv("DATABASE_PATH", "data/signals.db")),
        telegram_session_name=os.getenv("TELEGRAM_SESSION_NAME", "tele_scraper_brain").strip(),
    )
