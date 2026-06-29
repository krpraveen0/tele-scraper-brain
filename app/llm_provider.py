from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Protocol

import requests

from app.config import Settings
from app.models import SignalAnalysis, parse_analysis

DEFAULT_PROMPT_PATH = Path("prompts/classify_message.txt")
MESSAGE_PLACEHOLDER = "{message_text}"


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


class SignalAnalyzer(Protocol):
    def analyze(self, message_text: str) -> SignalAnalysis:
        ...


def load_prompt_template(path: Path = DEFAULT_PROMPT_PATH) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return DEFAULT_PROMPT


def render_prompt(template: str, message_text: str) -> str:
    """Render the message placeholder without interpreting JSON braces in the prompt."""
    return template.replace(MESSAGE_PLACEHOLDER, message_text)


def _parse_json_response(raw: str) -> SignalAnalysis:
    raw = raw.strip()
    if not raw:
        return SignalAnalysis.safe_default("LLM returned an empty response.")

    # OpenCode may return formatted text around JSON. Prefer direct JSON, then try to extract the outer object.
    try:
        return parse_analysis(json.loads(raw))
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return parse_analysis(json.loads(raw[start : end + 1]))
            except json.JSONDecodeError as exc:
                return SignalAnalysis.safe_default(f"Could not parse JSON object from LLM response: {exc}")
        return SignalAnalysis.safe_default("LLM response did not contain a JSON object.")


class OllamaAnalyzer:
    def __init__(self, base_url: str, model: str, prompt_path: Path = DEFAULT_PROMPT_PATH) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.prompt_template = load_prompt_template(prompt_path)

    def analyze(self, message_text: str) -> SignalAnalysis:
        prompt = render_prompt(self.prompt_template, message_text)
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
            return _parse_json_response(raw)
        except Exception as exc:  # noqa: BLE001 - user-facing resilience is preferred here.
            return SignalAnalysis.safe_default(f"Ollama analysis failed: {exc}")


class OpenCodeAnalyzer:
    """Use OpenCode's non-interactive CLI as the local analysis backend.

    OpenCode supports commands like:
        opencode run "Explain async/await"

    This adapter passes the rendered prompt as one CLI argument to avoid shell quoting issues.
    If OPENCODE_ATTACH_URL is configured, it runs through an already-started server:
        opencode serve
        opencode run --attach http://localhost:4096 "..."
    """

    def __init__(
        self,
        model: str = "",
        attach_url: str = "",
        timeout_seconds: int = 180,
        prompt_path: Path = DEFAULT_PROMPT_PATH,
    ) -> None:
        self.model = model
        self.attach_url = attach_url
        self.timeout_seconds = timeout_seconds
        self.prompt_template = load_prompt_template(prompt_path)

    def analyze(self, message_text: str) -> SignalAnalysis:
        prompt = render_prompt(self.prompt_template, message_text)
        command = ["opencode", "run", "--format", "json"]

        if self.attach_url:
            command.extend(["--attach", self.attach_url])
        if self.model:
            command.extend(["--model", self.model])

        command.append(prompt)

        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            if completed.returncode != 0:
                stderr = completed.stderr.strip() or "unknown OpenCode error"
                return SignalAnalysis.safe_default(f"OpenCode failed with exit code {completed.returncode}: {stderr}")

            return _parse_json_response(completed.stdout)
        except FileNotFoundError:
            return SignalAnalysis.safe_default("OpenCode CLI was not found. Install OpenCode or use LLM_PROVIDER=ollama.")
        except subprocess.TimeoutExpired:
            return SignalAnalysis.safe_default(f"OpenCode timed out after {self.timeout_seconds} seconds.")
        except Exception as exc:  # noqa: BLE001
            return SignalAnalysis.safe_default(f"OpenCode analysis failed: {exc}")


def create_analyzer(settings: Settings) -> SignalAnalyzer:
    if settings.llm_provider == "opencode":
        return OpenCodeAnalyzer(
            model=settings.opencode_model,
            attach_url=settings.opencode_attach_url,
            timeout_seconds=settings.opencode_timeout_seconds,
        )

    return OllamaAnalyzer(
        base_url=settings.ollama_url,
        model=settings.ollama_model,
    )
