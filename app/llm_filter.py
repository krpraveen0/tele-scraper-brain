from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from app.models import SignalAnalysis, parse_analysis

DEFAULT_PROMPT_PATH = Path("prompts/classify_message.txt")


def load_prompt_template(path: Path = DEFAULT_PROMPT_PATH) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return DEFAULT_PROMPT


DEFAULT_PROMPT = """
You are Praveen Signal OS, a personal information filter for Praveen Kumar.

Persona:
- Senior software/AI engineer working at a strong financial brand.
- Wants a future remote role with reliability, strong brand, and AI/full-stack growth.
- Builds and teaches Python, GenAI, agentic AI, RAG, local LLMs, and production AI systems.
- Writes on LinkedIn/Medium and wants practical technical content ideas.
- Practices spoken English and leadership communication.
- Tracks global economy and useful tools.

Analyze the Telegram message and return ONLY valid JSON.

Allowed categories:
Career, AI Engineering, Teaching, Content, English, Research, Tools, Global Economy, Other

Allowed suggested_action:
Read today, Read weekend, Apply, Prepare resume, Create LinkedIn post, Create Medium outline, Use in class, Create diagram, Practice speaking, Try tool, Archive, Ignore

JSON schema:
{
  "is_valuable": true,
  "score": 0-10,
  "category": "Career",
  "reason": "short reason",
  "summary": "short useful summary",
  "tags": ["#remotejob", "#ai"],
  "suggested_action": "Read today",
  "career_relevance": 0-10,
  "ai_engineering_relevance": 0-10,
  "teaching_usefulness": 0-10,
  "content_potential": 0-10,
  "english_usefulness": 0-10,
  "research_depth": 0-10,
  "urgency": 0-10,
  "noise_risk": 0-10
}

Message:
"""{message_text}"""
""".strip()


class OllamaFilter:
    def __init__(self, base_url: str, model: str, prompt_path: Path = DEFAULT_PROMPT_PATH) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.prompt_template = load_prompt_template(prompt_path)

    def analyze(self, message_text: str) -> SignalAnalysis:
        prompt = self.prompt_template.format(message_text=message_text)
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_ctx": 8192,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            raw = response.json().get("response", "{}")
            parsed = json.loads(raw)
            return parse_analysis(parsed)
        except Exception as exc:  # noqa: BLE001 - user-facing resilience is preferred here.
            return SignalAnalysis.safe_default(f"Ollama analysis failed: {exc}")
