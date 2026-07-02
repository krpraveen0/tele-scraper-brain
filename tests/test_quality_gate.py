from __future__ import annotations

from app.quality_gate import QualityGateReport, quality_rows, run_quality_gate


def test_quality_gate_marks_strong_draft_ready() -> None:
    text = """
# Signal to Blueprint

In a real workflow, the mistake I see is that teams save useful links but never convert them.

The trade-off is simple: more inputs create more noise unless one signal becomes a practical example.

Try this next: pick one saved signal and write the hidden gap before creating another draft.
"""

    report = run_quality_gate(text, surface="linkedin")

    assert isinstance(report, QualityGateReport)
    assert report.surface == "linkedin"
    assert report.ready_to_publish is True
    assert report.overall_score >= 7.0
    assert report.passed_checks >= 5
    assert report.failed_checks <= 2


def test_quality_gate_flags_empty_draft() -> None:
    report = run_quality_gate("", surface="general")

    assert report.ready_to_publish is False
    assert report.overall_score < 7.0
    assert any(check.name == "Draft exists" and not check.passed for check in report.checks)
    assert report.voice_review.score == 0.0


def test_quality_gate_detects_generic_hype() -> None:
    text = "In today's fast-paced world, this game-changer will revolutionize your workflow seamlessly."

    report = run_quality_gate(text, surface="medium")

    assert report.ready_to_publish is False
    assert any(check.name == "No generic AI hype" and not check.passed for check in report.checks)
    assert any("Generic AI phrases" in issue for issue in report.voice_review.issues)


def test_quality_rows_are_dashboard_friendly() -> None:
    report = run_quality_gate("In a real workflow, the trade-off is clarity versus speed. Try one example.")
    rows = quality_rows(report)

    assert rows
    assert {"check", "passed", "detail", "recommendation"}.issubset(rows[0].keys())
    assert all(isinstance(row["passed"], bool) for row in rows)


def test_render_contains_required_sections() -> None:
    report = run_quality_gate("In a real workflow, the mistake is skipping the trade-off. Try one example.")
    rendered = report.render()

    assert rendered.startswith("# Quality Gate Report")
    assert "Overall score" in rendered
    assert "## Checks" in rendered
    assert "## Voice Review" in rendered
    assert "Status:" in rendered
