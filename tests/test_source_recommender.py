from __future__ import annotations

from app.source_recommender import recommend_sources


def test_recommends_needs_more_data_for_small_sample() -> None:
    rec = recommend_sources(
        [
            {
                "source_title": "Small Source",
                "total": 4,
                "valuable": 2,
                "sent": 0,
                "avg_score": 7.5,
                "max_score": 9.0,
            }
        ],
        min_samples=10,
    )[0]

    assert rec.action == "needs_more_data"
    assert rec.suggested_min_save_score is None


def test_recommends_disable_for_no_value_low_scores() -> None:
    rec = recommend_sources(
        [
            {
                "source_title": "Noisy Source",
                "total": 25,
                "valuable": 0,
                "sent": 0,
                "avg_score": 2.5,
                "max_score": 5.5,
            }
        ]
    )[0]

    assert rec.action == "disable"
    assert rec.suggested_min_save_score == 9.0


def test_recommends_raise_threshold_for_low_signal_ratio() -> None:
    rec = recommend_sources(
        [
            {
                "source_title": "Weak Source",
                "total": 30,
                "valuable": 3,
                "sent": 1,
                "avg_score": 5.5,
                "max_score": 8.0,
            }
        ]
    )[0]

    assert rec.action == "raise_threshold"
    assert rec.suggested_min_save_score == 8.5


def test_recommends_keep_high_value_for_strong_source() -> None:
    rec = recommend_sources(
        [
            {
                "source_title": "Strong Source",
                "total": 30,
                "valuable": 15,
                "sent": 10,
                "avg_score": 7.4,
                "max_score": 9.5,
            }
        ]
    )[0]

    assert rec.action == "keep_high_value"
    assert rec.suggested_min_save_score == 7.0


def test_recommendations_prioritize_noisy_sources_first() -> None:
    recs = recommend_sources(
        [
            {"source_title": "Good", "total": 20, "valuable": 10, "sent": 5, "avg_score": 7.5, "max_score": 9.0},
            {"source_title": "Bad", "total": 20, "valuable": 0, "sent": 0, "avg_score": 1.0, "max_score": 4.0},
        ]
    )

    assert recs[0].source_title == "Bad"
    assert recs[0].action == "disable"
