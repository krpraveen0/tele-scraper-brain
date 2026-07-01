from __future__ import annotations

from app.blueprint_generator import ALLOWED_BLUEPRINT_TYPES, Blueprint, generate_blueprint, normalize_blueprint_type
from app.idea_lab import generate_idea_lab_report
from app.models import SignalAnalysis, StoredSignal


def make_stored_signal() -> StoredSignal:
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
            category="AI Engineering",
            reason="Useful creator and AI engineering signal.",
            summary="A useful agent workflow for memory, routing, evaluation and context engineering patterns.",
            tags=["#agents", "#context"],
            suggested_action="Create Medium outline",
        ),
        saved_to_telegram=False,
        created_at="2026-06-30T10:00:00+00:00",
    )


def make_report():
    return generate_idea_lab_report(make_stored_signal())


def test_generates_all_supported_blueprint_types() -> None:
    report = make_report()

    for blueprint_type in ALLOWED_BLUEPRINT_TYPES:
        blueprint = generate_blueprint(report, blueprint_type)

        assert isinstance(blueprint, Blueprint)
        assert blueprint.signal_id == report.signal_id
        assert blueprint.source == report.source
        assert blueprint.blueprint_type == blueprint_type
        assert blueprint.title
        assert blueprint.audience
        assert blueprint.promise
        assert blueprint.opening_scene
        assert blueprint.unique_angle
        assert blueprint.framework
        assert blueprint.sections
        assert blueprint.diagram_idea
        assert blueprint.conclusion
        assert blueprint.call_to_action
        assert blueprint.quality_checklist


def test_normalizes_blueprint_type_variants() -> None:
    assert normalize_blueprint_type("tech-blog") == "tech_blog"
    assert normalize_blueprint_type("deep article") == "deep_article"
    assert normalize_blueprint_type("COURSE_MODULE") == "course_module"


def test_rejects_unknown_blueprint_type() -> None:
    try:
        generate_blueprint(make_report(), "random")
    except ValueError as exc:
        assert "Unsupported blueprint type" in str(exc)
        assert "tech_blog" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported blueprint type")


def test_blueprint_render_contains_required_sections() -> None:
    blueprint = generate_blueprint(make_report(), "tech_blog")
    rendered = blueprint.render()

    assert rendered.startswith("# ")
    assert "## Audience" in rendered
    assert "## Promise" in rendered
    assert "## Opening Scene" in rendered
    assert "## Unique Angle" in rendered
    assert "## Framework" in rendered
    assert "## Structure" in rendered
    assert "## Diagram Idea" in rendered
    assert "## Conclusion" in rendered
    assert "## Call To Action" in rendered
    assert "## Quality Checklist" in rendered


def test_course_module_blueprint_has_teaching_parts() -> None:
    blueprint = generate_blueprint(make_report(), "course_module")
    rendered = blueprint.render().lower()

    assert "learning outcome" in rendered
    assert "hands-on" in rendered
    assert "assessment" in rendered
    assert "trainer" in rendered or "learner" in rendered


def test_storybook_blueprint_has_story_parts() -> None:
    blueprint = generate_blueprint(make_report(), "storybook_chapter")
    rendered = blueprint.render().lower()

    assert "characters" in rendered
    assert "conflict" in rendered
    assert "failure" in rendered
    assert "lesson" in rendered


def test_podcast_blueprint_has_spoken_episode_parts() -> None:
    blueprint = generate_blueprint(make_report(), "podcast_script")
    rendered = blueprint.render().lower()

    assert "cold open" in rendered
    assert "episode" in rendered
    assert "listener" in rendered
    assert "readable aloud" in rendered


def test_deep_article_blueprint_includes_tradeoffs() -> None:
    blueprint = generate_blueprint(make_report(), "deep_article")
    rendered = blueprint.render().lower()

    assert "design options" in rendered
    assert "trade-off" in rendered
    assert "failure mode" in rendered
