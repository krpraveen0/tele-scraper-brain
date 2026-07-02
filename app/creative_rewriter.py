from __future__ import annotations

from dataclasses import dataclass
import subprocess
from typing import Protocol

import requests

from app.config import Settings
from app.voice_profile import VoiceReview, build_voice_prompt, review_voice


ALLOWED_REWRITE_INTENTS = {
    "polish",
    "humanize",
    "make_practical",
    "shorten",
    "expand",
    "linkedin_ready",
    "medium_ready",
    "course_ready",
    "podcast_ready",
    "storybook_ready",
}


@dataclass(frozen=True)
class RewriteRequest:
    draft: str
    surface: str = "general"
    intent: str = "humanize"
    source_context: str = ""
    constraints: list[str] | None = None


@dataclass(frozen=True)
class RewriteResult:
    original: str
    rewritten: str
    surface: str
    intent: str
    voice_review: VoiceReview

    def render(self) -> str:
        return "\n".join(
            [
                "# Creative Rewrite Result",
                "",
                f"Surface: {self.surface}",
                f"Intent: {self.intent}",
                f"Voice score: {self.voice_review.score:.1f}/10",
                "",
                "## Rewritten Draft",
                self.rewritten,
                "",
                "## Voice Review",
                self.voice_review.render(),
            ]
        ).strip()


class CreativeRewriter(Protocol):
    def rewrite(self, request: RewriteRequest) -> RewriteResult:
        ...


def normalize_rewrite_intent(value: str) -> str:
    normalized = str(value or "humanize").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_REWRITE_INTENTS:
        allowed = ", ".join(sorted(ALLOWED_REWRITE_INTENTS))
        raise ValueError(f"Unsupported rewrite intent '{value}'. Allowed intents: {allowed}")
    return normalized


def build_creative_rewrite_prompt(request: RewriteRequest) -> str:
    intent = normalize_rewrite_intent(request.intent)
    constraints = request.constraints or []
    lines = [
        build_voice_prompt(request.surface),
        "",
        "Rewrite task:",
        f"- Intent: {intent}",
        "- Rewrite the draft in Praveen's voice.",
        "- Keep the meaning and source facts intact.",
        "- Do not invent metrics, companies, personal stories, or citations.",
        "- Return only the rewritten Markdown. Do not wrap in code fences.",
    ]
    if request.source_context.strip():
        lines.extend(["", "Source context:", request.source_context.strip()[:3000]])
    if constraints:
        lines.extend(["", "Extra constraints:"])
        lines.extend(f"- {constraint}" for constraint in constraints if constraint.strip())
    lines.extend(["", "Draft to rewrite:", request.draft.strip()])
    return "\n".join(lines).strip()


class OllamaCreativeRewriter:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def rewrite(self, request: RewriteRequest) -> RewriteResult:
        prompt = build_creative_rewrite_prompt(request)
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.35, "num_ctx": 8192},
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        text = str(response.json().get("response", "")).strip()
        if not text:
            raise RuntimeError("Ollama returned an empty creative rewrite.")
        return build_rewrite_result(request, text)


class OpenCodeCreativeRewriter:
    def __init__(self, model: str = "", attach_url: str = "", timeout_seconds: int = 180) -> None:
        self.model = model
        self.attach_url = attach_url
        self.timeout_seconds = timeout_seconds

    def rewrite(self, request: RewriteRequest) -> RewriteResult:
        prompt = build_creative_rewrite_prompt(request)
        command = ["opencode", "run"]
        if self.attach_url:
            command.extend(["--attach", self.attach_url])
        if self.model:
            command.extend(["--model", self.model])
        command.append(prompt)

        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or "unknown OpenCode error"
            raise RuntimeError(f"OpenCode failed with exit code {completed.returncode}: {stderr}")
        text = completed.stdout.strip()
        if not text:
            raise RuntimeError("OpenCode returned an empty creative rewrite.")
        return build_rewrite_result(request, text)


def create_creative_rewriter(settings: Settings) -> CreativeRewriter:
    if settings.llm_provider == "opencode":
        return OpenCodeCreativeRewriter(
            model=settings.opencode_model,
            attach_url=settings.opencode_attach_url,
            timeout_seconds=settings.opencode_timeout_seconds,
        )
    return OllamaCreativeRewriter(base_url=settings.ollama_url, model=settings.ollama_model)


def build_rewrite_result(request: RewriteRequest, rewritten_text: str) -> RewriteResult:
    rewritten = rewritten_text.strip()
    if not rewritten:
        raise ValueError("Rewritten text is empty.")
    intent = normalize_rewrite_intent(request.intent)
    voice = review_voice(rewritten, surface=request.surface)
    return RewriteResult(
        original=request.draft.strip(),
        rewritten=rewritten,
        surface=voice.surface,
        intent=intent,
        voice_review=voice,
    )
