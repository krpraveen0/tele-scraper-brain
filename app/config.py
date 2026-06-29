from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    tg_api_id: int
    tg_api_hash: str
    tg_phone: str
    source_chats: list[str]
    destination_chat: str
    briefing_chat: str
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


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def load_settings() -> Settings:
    load_dotenv()

    source_chats = _split_csv(os.getenv("SOURCE_CHATS", ""))
    destination_chat = os.getenv("DESTINATION_CHAT", "").strip()
    briefing_chat = os.getenv("BRIEFING_CHAT", "").strip() or destination_chat
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    if llm_provider not in {"ollama", "opencode"}:
        raise RuntimeError("LLM_PROVIDER must be either 'ollama' or 'opencode'.")

    missing = []
    for key in ["TG_API_ID", "TG_API_HASH", "TG_PHONE", "SOURCE_CHATS", "DESTINATION_CHAT"]:
        if not os.getenv(key):
            missing.append(key)

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
        llm_provider=llm_provider,
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip(),
        opencode_model=os.getenv("OPENCODE_MODEL", "").strip(),
        opencode_attach_url=os.getenv("OPENCODE_ATTACH_URL", "").strip(),
        opencode_timeout_seconds=int(os.getenv("OPENCODE_TIMEOUT_SECONDS", "180")),
        min_save_score=float(os.getenv("MIN_SAVE_SCORE", "7.0")),
        max_message_chars=int(os.getenv("MAX_MESSAGE_CHARS", "5000")),
        database_path=Path(os.getenv("DATABASE_PATH", "data/signals.db")),
        telegram_session_name=os.getenv("TELEGRAM_SESSION_NAME", "tele_scraper_brain").strip(),
    )
