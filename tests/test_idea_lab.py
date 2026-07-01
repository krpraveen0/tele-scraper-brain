from __future__ import annotations

from app.idea_lab import ANGLE_TYPES, IdeaLabReport, generate_idea_lab_report
from app.models import SignalAnalysis, StoredSignal


def make_stored_signal(
    category: str = "AI Engineering",
    suggested_action: str = "Create Medium outline",
    tags: list[str] | None = None,
) -> StoredSignal:
    resolved_tags = ["#agents", "#context"] if tags is None else tags
    return StoredSignal(
        id=42,
        source_id="source-1",
        source_title="GitHub Community",
        message_id=100,
        message_text="New agent workflow shows memory, routing, evaluation and context engineering patterns.",
        message_date="2026-06-30T10:00:00+00:00",
        permalink="https://t.me/test/100",
        analysis=SignalAnalysis(
            is_valuable=True,
            score=8.5,
            category=category,
            reason="Useful creator and AI engineering signal.",
            summary="A useful agent workflow for memory, routing, evaluation and context engineering patterns.",
            tags=resolved_tags,
            suggested_action=suggested_action,
        ),
        saved_to_telegram=False,
        created_at="2026-06-30T10:00:00+00:00",
    )


def test_generates_idea_lab_report_shape() -> None:
    signal = make_stored_signal()
    report = generate_idea_lab_report(signal)

    assert isinstance(report, IdeaLabReport)
    assert report.signal_id == signal.id
    assert report.source == "GitHub Community"
    assert report.category == "AI Engineering"
    assert report.core_insight
    assert report.hidden_gap
    assert report.novel_angle
    assert report.recommended_format == "Medium article blueprint"


def test_generates_all_required_angle_types() -> None:
    report = generate_idea_lab_report(make_stored_signal())

    assert len(report.content_angles) == 10
    assert tuple(angle.angle_type for angle in report.content_angles) == ANGLE_TYPES
    assert all(angle.title for angle in report.content_angles)
    assert all(angle.target_audience for angle in report.content_angles)
    assert all(angle.description for angle in report.content_angles)


def test_generates_content_seeds_for_target_formats() -> None:
    report = generate_idea_lab_report(make_stored_signal())
    seed_types = {seed.seed_type for seed in report.seeds}

    assert seed_types == {"blog_seed", "course_seed", "podcast_seed", "storybook_seed"}
    assert all(seed.title for seed in report.seeds)
    assert all(len(seed.outline) >= 4 for seed in report.seeds)


def test_report_render_contains_main_sections() -> None:
    report = generate_idea_lab_report(make_stored_signal())
    rendered = report.render()

    assert rendered.startswith("# Idea Lab Report")
    assert "## Core Insight" in rendered
    assert "## Hidden Gap" in rendered
    assert "## Novel Angle" in rendered
    assert "## Content Angles" in rendered
    assert "## Title Ideas" in rendered
    assert "## Diagram Ideas" in rendered
    assert "## Content Seeds" in rendered
    assert "## Quality Checklist" in rendered


def test_recommended_format_uses_action_and_category() -> None:
    assert generate_idea_lab_report(make_stored_signal(suggested_action="Create LinkedIn post")).recommended_format == "LinkedIn post"
    assert generate_idea_lab_report(make_stored_signal(category="Teaching", suggested_action="Use in class")).recommended_format == "Course module"
    assert generate_idea_lab_report(make_stored_signal(category="Tools", suggested_action="Try tool")).recommended_format == "Tool review"
    assert generate_idea_lab_report(make_stored_signal(category="English", suggested_action="Practice speaking")).recommended_format == "Speaking practice script"


def test_report_uses_category_as_topic_when_tags_are_missing() -> None:
    report = generate_idea_lab_report(make_stored_signal(category="Career", suggested_action="Apply", tags=[]))

    assert "career" in report.title_ideas[1].lower()
    assert report.recommended_format == "Career note"


def test_quality_checklist_supports_creator_gates() -> None:
    report = generate_idea_lab_report(make_stored_signal())
    checklist_text = " ".join(report.quality_checklist).lower()

    assert "non-obvious" in checklist_text
    assert "reader pain" in checklist_text
    assert "trade-off" in checklist_text
    assert "blog" in checklist_text
    assert "course" in checklist_text
    assert "podcast" in checklist_text
    assert "story" in checklist_text
