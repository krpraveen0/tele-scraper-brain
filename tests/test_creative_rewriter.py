from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.creative_rewriter import (
    OllamaCreativeRewriter,
    OpenCodeCreativeRewriter,
    RewriteRequest,
    build_creative_rewrite_prompt,
    build_rewrite_result,
    create_creative_rewriter,
    normalize_rewrite_intent,
)


@dataclass(frozen=True)
class DummySettings:
    llm_provider: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    opencode_model: str = ""
    opencode_attach_url: str = ""
    opencode_timeout_seconds: int = 180


def test_normalize_rewrite_intent_accepts_human_friendly_values() -> None:
    assert normalize_rewrite_intent("make practical") == "make_practical"
    assert normalize_rewrite_intent("linkedin-ready") == "linkedin_ready"
    assert normalize_rewrite_intent("humanize") == "humanize"


def test_invalid_rewrite_intent_is_rejected() -> None:
    try:
        normalize_rewrite_intent("random")
    except ValueError as exc:
        assert "Unsupported rewrite intent" in str(exc)
        assert "humanize" in str(exc)
    else:
        raise AssertionError("Expected invalid rewrite intent to fail")


def test_build_creative_rewrite_prompt_contains_voice_and_constraints() -> None:
    prompt = build_creative_rewrite_prompt(
        RewriteRequest(
            draft="This is a generic AI draft.",
            surface="linkedin",
            intent="make_practical",
            source_context="Original signal context.",
            constraints=["Keep it under 120 words.", "Use one trade-off."],
        )
    )

    assert "Write in Praveen's voice." in prompt
    assert "Surface guidance for linkedin" in prompt
    assert "Intent: make_practical" in prompt
    assert "Original signal context." in prompt
    assert "Keep it under 120 words." in prompt
    assert "This is a generic AI draft." in prompt
    assert "Do not invent metrics" in prompt


def test_build_rewrite_result_scores_voice() -> None:
    request = RewriteRequest(draft="Old draft", surface="linkedin", intent="humanize")
    rewritten = "In a real workflow, the mistake I see is saving links without converting them. The trade-off is more noise."

    result = build_rewrite_result(request, rewritten)

    assert result.original == "Old draft"
    assert result.rewritten == rewritten
    assert result.surface == "linkedin"
    assert result.intent == "humanize"
    assert result.voice_review.score >= 8.0
    assert "# Creative Rewrite Result" in result.render()


def test_build_rewrite_result_rejects_empty_rewrite() -> None:
    try:
        build_rewrite_result(RewriteRequest(draft="Old draft"), "")
    except ValueError as exc:
        assert "Rewritten text is empty" in str(exc)
    else:
        raise AssertionError("Expected empty rewrite to fail")


def test_create_creative_rewriter_selects_ollama() -> None:
    rewriter = create_creative_rewriter(DummySettings())  # type: ignore[arg-type]

    assert isinstance(rewriter, OllamaCreativeRewriter)


def test_create_creative_rewriter_selects_opencode() -> None:
    settings = DummySettings(llm_provider="opencode", opencode_model="test-model", opencode_timeout_seconds=5)
    rewriter = create_creative_rewriter(settings)  # type: ignore[arg-type]

    assert isinstance(rewriter, OpenCodeCreativeRewriter)
    assert rewriter.model == "test-model"
    assert rewriter.timeout_seconds == 5


def test_ollama_rewriter_uses_generate_endpoint(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"response": "In a real workflow, the trade-off is clarity versus speed."}

    def fake_post(url: str, json: dict[str, object], timeout: int):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr("app.creative_rewriter.requests.post", fake_post)
    rewriter = OllamaCreativeRewriter("http://localhost:11434", "model-a", timeout_seconds=7)
    result = rewriter.rewrite(RewriteRequest(draft="Old", surface="medium"))

    assert calls[0]["url"] == "http://localhost:11434/api/generate"
    assert calls[0]["timeout"] == 7
    assert "model-a" == calls[0]["json"]["model"]  # type: ignore[index]
    assert result.surface == "medium"
    assert "trade-off" in result.rewritten


def test_opencode_rewriter_builds_command(monkeypatch) -> None:
    calls: list[list[str]] = []

    class Completed:
        returncode = 0
        stdout = "In a real workflow, the mistake is skipping the trade-off."
        stderr = ""

    def fake_run(command, check, capture_output, text, timeout):
        calls.append(command)
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == 9
        return Completed()

    monkeypatch.setattr("app.creative_rewriter.subprocess.run", fake_run)
    rewriter = OpenCodeCreativeRewriter(model="model-b", attach_url="https://example.com", timeout_seconds=9)
    result = rewriter.rewrite(RewriteRequest(draft="Old", surface="course"))

    assert calls[0][:2] == ["opencode", "run"]
    assert "--attach" in calls[0]
    assert "--model" in calls[0]
    assert result.surface == "course"
    assert "trade-off" in result.rewritten
