from __future__ import annotations

from app.voice_profile import (
    VoiceProfile,
    build_voice_prompt,
    default_praveen_voice_profile,
    normalize_surface,
    review_voice,
)


def test_default_profile_shape() -> None:
    profile = default_praveen_voice_profile()

    assert isinstance(profile, VoiceProfile)
    assert profile.name == "Praveen Voice Profile"
    assert "AI engineer" in profile.positioning
    assert profile.tone_rules
    assert profile.structure_rules
    assert profile.preferred_phrases
    assert profile.banned_phrases
    assert "linkedin" in profile.surface_guidance


def test_profile_render_includes_surface_guidance() -> None:
    rendered = default_praveen_voice_profile().render("linkedin")

    assert rendered.startswith("# Praveen Voice Profile")
    assert "## Positioning" in rendered
    assert "## Tone Rules" in rendered
    assert "## Structure Rules" in rendered
    assert "Surface Guidance: linkedin" in rendered
    assert "Avoid sounding like a polished AI announcement" in rendered


def test_normalize_surface_accepts_human_friendly_values() -> None:
    assert normalize_surface("LinkedIn") == "linkedin"
    assert normalize_surface("story book") == "storybook"
    assert normalize_surface("general") == "general"


def test_invalid_surface_is_rejected() -> None:
    try:
        normalize_surface("twitter")
    except ValueError as exc:
        assert "Unsupported voice surface" in str(exc)
        assert "linkedin" in str(exc)
    else:
        raise AssertionError("Expected invalid surface to fail")


def test_review_rewards_practical_builder_voice() -> None:
    text = (
        "In a real workflow, the mistake I see is that teams save links but never convert them. "
        "The trade-off is simple: more inputs create more noise unless we turn one signal into an example."
    )

    review = review_voice(text, surface="linkedin")

    assert review.score >= 8.0
    assert any("practical" in item.lower() for item in review.strengths)
    assert not review.issues


def test_review_penalizes_generic_ai_hype() -> None:
    text = "In today's fast-paced world, this game-changer will revolutionize your workflow seamlessly."

    review = review_voice(text, surface="medium")

    assert review.score < 8.0
    assert any("Generic AI phrases" in item for item in review.issues)
    assert any("Replace hype" in item for item in review.suggestions)


def test_review_handles_empty_text() -> None:
    review = review_voice("", surface="general")

    assert review.score == 0.0
    assert review.issues == ["Text is empty."]
    assert review.suggestions == ["Add a draft before reviewing voice."]


def test_build_voice_prompt_contains_rules_and_banned_phrases() -> None:
    prompt = build_voice_prompt("course")

    assert "Write in Praveen's voice." in prompt
    assert "trainer-friendly steps" in prompt
    assert "game-changer" in prompt
    assert "Tone rules:" in prompt
