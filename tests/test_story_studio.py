from __future__ import annotations

from app.idea_lab import generate_idea_lab_report
from app.models import SignalAnalysis, StoredSignal
from app.story_studio import StoryDraft, generate_story, normalize_story_format, normalize_story_tone


def make_report():
    signal = StoredSignal(
        id=42,
        source_id="source-1",
        source_title="GitHub Community",
        message_id=100,
        message_text="Agent workflow signal with memory, routing, evaluation and context patterns.",
        message_date="2026-06-30T10:00:00+00:00",
        permalink="https://t.me/test/100",
        analysis=SignalAnalysis(
            is_valuable=True,
            score=8.5,
            category="AI Engineering",
            reason="Useful creator and AI engineering signal.",
            summary="A useful agent workflow signal.",
            tags=["#agents", "#context"],
            suggested_action="Create Medium outline",
        ),
        saved_to_telegram=False,
        created_at="2026-06-30T10:00:00+00:00",
    )
    return generate_idea_lab_report(signal)


def test_generates_story_draft_shape() -> None:
    report = make_report()
    story = generate_story(report)

    assert isinstance(story, StoryDraft)
    assert story.signal_id == report.signal_id
    assert story.source == report.source
    assert story.format == "chapter"
    assert story.tone == "practical"
    assert story.title
    assert story.premise
    assert story.lesson
    assert len(story.characters) == 3
    assert len(story.scenes) == 4
    assert story.reuse_notes
    assert story.quality_checklist


def test_normalizers_accept_human_friendly_values() -> None:
    assert normalize_story_format("case study") == "case_study"
    assert normalize_story_format("dialogue") == "dialogue"
    assert normalize_story_tone("Mentor") == "mentor"
    assert normalize_story_tone("reflective") == "reflective"


def test_invalid_inputs_are_rejected() -> None:
    try:
        generate_story(make_report(), story_format="novel")
    except ValueError as exc:
        assert "Unsupported story format" in str(exc)
    else:
        raise AssertionError("Expected invalid story format to fail")

    try:
        generate_story(make_report(), tone="funny")
    except ValueError as exc:
        assert "Unsupported story tone" in str(exc)
    else:
        raise AssertionError("Expected invalid story tone to fail")


def test_scene_format_is_shorter_than_chapter() -> None:
    chapter = generate_story(make_report(), story_format="chapter")
    scene = generate_story(make_report(), story_format="scene")

    assert len(chapter.scenes) == 4
    assert len(scene.scenes) == 2


def test_dialogue_format_has_three_scenes() -> None:
    story = generate_story(make_report(), story_format="dialogue")

    assert story.format == "dialogue"
    assert len(story.scenes) == 3
    assert "Dialogue" in story.title


def test_mentor_tone_changes_hook_and_character() -> None:
    story = generate_story(make_report(), tone="mentor")

    assert story.tone == "mentor"
    assert story.characters[0].name == "Mira"
    assert "what will this change" in story.opening_hook.lower()


def test_render_contains_required_sections() -> None:
    rendered = generate_story(make_report(), story_format="case_study", tone="reflective").render()

    assert rendered.startswith("# ")
    assert "## Premise" in rendered
    assert "## Lesson" in rendered
    assert "## Characters" in rendered
    assert "## Opening Hook" in rendered
    assert "## Scenes" in rendered
    assert "## Closing Reflection" in rendered
    assert "## Reuse Notes" in rendered
    assert "## Quality Checklist" in rendered
