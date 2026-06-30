from __future__ import annotations

from app.models import SignalAnalysis, parse_analysis


def test_parse_analysis_normalizes_scores_categories_actions_and_tags() -> None:
    analysis = parse_analysis(
        {
            "is_valuable": True,
            "score": 99,
            "category": "UnknownCategory",
            "suggested_action": "UnsupportedAction",
            "tags": ["Remote Job", "AI", "", "Research Paper"],
            "noise_risk": -5,
        }
    )

    assert analysis.is_valuable is True
    assert analysis.score == 10.0
    assert analysis.category == "Other"
    assert analysis.suggested_action == "Archive"
    assert analysis.tags == ["#remotejob", "#ai", "#researchpaper"]
    assert analysis.noise_risk == 0.0


def test_analysis_json_round_trip() -> None:
    original = SignalAnalysis(
        is_valuable=True,
        score=8.0,
        category="AI Engineering",
        reason="Useful production AI pattern.",
        summary="Explains traces for agent workflows.",
        tags=["#agenticai"],
        suggested_action="Read today",
    )

    restored = SignalAnalysis.from_json(original.to_json())

    assert restored == original
