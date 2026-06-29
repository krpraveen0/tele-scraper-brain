from __future__ import annotations

import re

_URL_RE = re.compile(r"https?://\S+")
_WHITESPACE_RE = re.compile(r"\s+")


def clean_message(text: str, max_chars: int = 5000) -> str:
    """Normalize Telegram text while preserving enough context for the LLM."""
    text = text or ""
    text = text.replace("\u200b", " ").replace("\xa0", " ")
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + " ..."
    return text


def canonicalize_for_hash(text: str) -> str:
    """Create a stable text form for duplicate detection across reposted messages."""
    normalized = clean_message(text, max_chars=10000).lower()
    normalized = _URL_RE.sub("", normalized)
    normalized = re.sub(r"[^a-z0-9#+.\- ]+", " ", normalized)
    normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
    return normalized
