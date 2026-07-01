from __future__ import annotations

from app.course_factory import CourseModule, generate_course_module, normalize_course_format, normalize_course_level
from app.idea_lab import generate_idea_lab_report
from app.models import SignalAnalysis, StoredSignal


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


def test_generates_course_module_shape() -> None:
    module = generate_course_module(make_report())

    assert isinstance(module, CourseModule)
    assert module.level == "intermediate"
    assert module.format == "workshop"
    assert module.learning_outcome
    assert module.prerequisites
    assert module.demo_steps
    assert module.activities
    assert module.assessment
    assert module.trainer_notes


def test_normalizers_accept_human_friendly_values() -> None:
    assert normalize_course_level("Beginner") == "beginner"
    assert normalize_course_level("advanced") == "advanced"
    assert normalize_course_format("mini project") == "mini_project"
    assert normalize_course_format("assessment") == "assessment"


def test_invalid_inputs_are_rejected() -> None:
    try:
        generate_course_module(make_report(), level="expert")
    except ValueError as exc:
        assert "Unsupported course level" in str(exc)
    else:
        raise AssertionError("Expected invalid level to fail")

    try:
        generate_course_module(make_report(), course_format="webinar")
    except ValueError as exc:
        assert "Unsupported course format" in str(exc)
    else:
        raise AssertionError("Expected invalid format to fail")


def test_render_contains_required_sections() -> None:
    rendered = generate_course_module(make_report()).render()

    assert "## Target Learners" in rendered
    assert "## Learning Outcome" in rendered
    assert "## Concept Explanation" in rendered
    assert "## Activities" in rendered
    assert "## Assessment" in rendered
    assert "## Trainer Notes" in rendered


def test_mini_project_format_includes_project_activity() -> None:
    module = generate_course_module(make_report(), course_format="mini_project")
    titles = [activity.title for activity in module.activities]

    assert "Mini Project: Build a Signal-to-Blueprint Board" in titles
    assert len(module.activities) == 3


def test_advanced_level_adds_deeper_trainer_note() -> None:
    module = generate_course_module(make_report(), level="advanced")
    notes = " ".join(module.trainer_notes).lower()

    assert "trade-offs" in notes
    assert "failure modes" in notes
    assert "system impact" in notes
