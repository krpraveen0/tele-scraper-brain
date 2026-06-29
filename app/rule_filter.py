from __future__ import annotations

from dataclasses import dataclass


NOISE_KEYWORDS = {
    "good morning",
    "good night",
    "gm ",
    "100% guarantee",
    "earn money fast",
    "crypto pump",
    "join fast",
    "limited seats hurry",
    "double your money",
    "whatsapp group link",
    "free recharge",
}

IMPORTANT_KEYWORDS = {
    "remote",
    "hiring",
    "job",
    "engineer",
    "full stack",
    "full-stack",
    "python",
    "next.js",
    "react",
    "llm",
    "rag",
    "agent",
    "agentic",
    "langchain",
    "langgraph",
    "ollama",
    "local llm",
    "research paper",
    "paper",
    "open source",
    "github",
    "funding",
    "startup",
    "course",
    "tutorial",
    "global economy",
    "inflation",
    "fed",
    "market",
    "observability",
    "tracing",
    "eval",
    "evaluation",
    "voice ai",
    "tool",
}


@dataclass(frozen=True)
class RuleDecision:
    should_analyze: bool
    reason: str


def should_send_to_llm(text: str) -> RuleDecision:
    lowered = f" {text.lower()} "

    if len(text.strip()) < 40:
        return RuleDecision(False, "Too short to be useful")

    for keyword in NOISE_KEYWORDS:
        if keyword in lowered:
            return RuleDecision(False, f"Noise keyword matched: {keyword}")

    for keyword in IMPORTANT_KEYWORDS:
        if keyword in lowered:
            return RuleDecision(True, f"Important keyword matched: {keyword}")

    # Keep some medium-length posts because useful posts may not contain obvious keywords.
    if len(text) > 280:
        return RuleDecision(True, "Long enough to deserve analysis")

    return RuleDecision(False, "No useful signal detected by rule filter")
