from __future__ import annotations

from app.asset_generator import ALLOWED_ASSET_TYPES, generate_asset
from app.models import SignalAnalysis, StoredSignal


def make_stored_signal() -> StoredSignal:
    return StoredSignal(
        id=42,
        source_id="source-1",
        source_title="GitHub Community",
        message_id=100,
        message_text="New LangGraph repo shows agent memory, routing and evaluation patterns.",
        message_date="2026-06-30T10:00:00+00:00",
        permalink="https://t.me/test/100",
        analysis=SignalAnalysis(
            is_valuable=True,
            score=8.5,
            category="AI Engineering",
            reason="Useful agentic AI architecture signal.",
            summary="A useful LangGraph repo for agent memory and evaluation patterns.",
            tags=["#agents", "#rag"],
            suggested_action="Try tool",
        ),
        saved_to_telegram=False,
        created_at="2026-06-30T10:00:00+00:00",
    )


def test_generates_all_supported_asset_types() -> None:
    signal = make_stored_signal()

    for asset_type in ALLOWED_ASSET_TYPES:
        asset = generate_asset(signal, asset_type)

        assert asset.signal_id == signal.id
        assert asset.asset_type == asset_type
        assert asset.title
        assert "GitHub Community" in asset.body
        assert asset.render().startswith("# ")


def test_accepts_asset_type_with_hyphen() -> None:
    asset = generate_asset(make_stored_signal(), "medium-outline")

    assert asset.asset_type == "medium_outline"
    assert "Medium" in asset.title


def test_rejects_unknown_asset_type() -> None:
    signal = make_stored_signal()

    try:
        generate_asset(signal, "random")
    except ValueError as exc:
        assert "Unsupported asset type" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported asset type")


def test_linkedin_asset_contains_personal_signal_os_frame() -> None:
    asset = generate_asset(make_stored_signal(), "linkedin")

    assert "Signal OS" in asset.body
    assert "feedback-driven" in asset.body


def test_english_practice_asset_contains_speaking_task() -> None:
    asset = generate_asset(make_stored_signal(), "english_practice")

    assert "Say this in 30 seconds" in asset.body
    assert "The key takeaway is" in asset.body
