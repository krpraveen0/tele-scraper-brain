from __future__ import annotations

from app.idea_lab import generate_idea_lab_report
from app.models import SignalAnalysis, StoredSignal
from app.series_builder import ALLOWED_SERIES_TYPES, ContentSeries, generate_series, normalize_episode_count, normalize_series_type


def make_report():
    signal = StoredSignal(
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
    return generate_idea_lab_report(signal)


def test_generates_all_supported_series_types() -> None:
    report = make_report()

    for series_type in ALLOWED_SERIES_TYPES:
        series = generate_series(report, series_type)

        assert isinstance(series, ContentSeries)
        assert series.signal_id == report.signal_id
        assert series.source == report.source
        assert series.series_type == series_type
        assert len(series.episodes) == 5
        assert series.title
        assert series.audience
        assert series.promise
        assert series.narrative_arc
        assert series.reuse_plan
        assert series.quality_checklist


def test_episode_count_can_be_customized() -> None:
    series = generate_series(make_report(), "linkedin_series", episode_count=3)

    assert len(series.episodes) == 3
    assert [episode.index for episode in series.episodes] == [1, 2, 3]


def test_normalizers_accept_human_friendly_values() -> None:
    assert normalize_series_type("linkedin series") == "linkedin_series"
    assert normalize_series_type("medium-series") == "medium_series"
    assert normalize_episode_count(10) == 10


def test_invalid_series_type_is_rejected() -> None:
    try:
        generate_series(make_report(), "random")
    except ValueError as exc:
        assert "Unsupported series type" in str(exc)
        assert "linkedin_series" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid series type")


def test_invalid_episode_count_is_rejected() -> None:
    try:
        generate_series(make_report(), "linkedin_series", episode_count=2)
    except ValueError as exc:
        assert "between 3 and 10" in str(exc)
    else:
        raise AssertionError("Expected ValueError for too few episodes")


def test_render_contains_required_sections() -> None:
    series = generate_series(make_report(), "medium_series")
    rendered = series.render()

    assert rendered.startswith("# ")
    assert "## Audience" in rendered
    assert "## Promise" in rendered
    assert "## Narrative Arc" in rendered
    assert "## Episodes" in rendered
    assert "## Reuse Plan" in rendered
    assert "## Quality Checklist" in rendered
    assert "### Episode 1" in rendered


def test_course_series_has_course_specific_quality() -> None:
    series = generate_series(make_report(), "course_series")
    checklist = " ".join(series.quality_checklist).lower()

    assert "learner task" in checklist
    assert "course" in series.title.lower()
    assert all(episode.format == "Course lesson" for episode in series.episodes)


def test_storybook_series_has_story_arc() -> None:
    series = generate_series(make_report(), "storybook_series")

    assert "Character" in series.narrative_arc
    assert "conflict" in " ".join(series.quality_checklist).lower()
    assert all(episode.format == "Story chapter" for episode in series.episodes)


def test_podcast_series_is_speakable() -> None:
    series = generate_series(make_report(), "podcast_series")

    assert "speakable" in " ".join(series.quality_checklist).lower()
    assert all(episode.format == "Podcast episode" for episode in series.episodes)
