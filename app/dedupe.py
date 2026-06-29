from __future__ import annotations

import hashlib

from app.message_cleaner import canonicalize_for_hash


def content_hash(text: str) -> str:
    canonical = canonicalize_for_hash(text)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
