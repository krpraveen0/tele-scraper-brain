from __future__ import annotations

from app.asset_generator import GeneratedAsset
from app.asset_rewriter import _asset_from_markdown, build_rewrite_prompt
from app.models import SignalAnalysis, StoredSignal


def make_signal() -> StoredSignal:
    return StoredSignal(
        id=7,
        source_id="source-1",
        source_title="Test Source",
        message_id=1,
        message_text="A useful AI engineering signal.",
        message_date="2026-06-30T10:00:00+00:00",
        permalink=None,
        analysis=SignalAnalysis(is_valuable=True, score=8.0, category="AI Engineering", summary="Useful AI signal."),
        saved_to_telegram=False,
        created_at="2026-06-30T10:00:00+00:00",
    )


def test_build_rewrite_prompt_contains_signal_and_asset_context() -> None:
    asset = GeneratedAsset(signal_id=7, asset_type="linkedin", title="LinkedIn Draft", body="Draft body")
    prompt = build_rewrite_prompt(make_signal(), asset)

    assert "Praveen Kumar" in prompt
    assert "linkedin" in prompt
    assert "Draft body" in prompt
    assert "Useful AI signal" in prompt


def test_asset_from_markdown_extracts_title() -> None:
    original = GeneratedAsset(signal_id=7, asset_type="linkedin", title="Old Title", body="Old body")
    rewritten = _asset_from_markdown(original, "# New Title\n\nNew body")

    assert rewritten.title == "New Title"
    assert rewritten.body == "New body"
    assert rewritten.asset_type == "linkedin"
    assert rewritten.signal_id == 7


def test_asset_from_markdown_keeps_original_title_without_heading() -> None:
    original = GeneratedAsset(signal_id=7, asset_type="tool_review", title="Tool Review", body="Old body")
    rewritten = _asset_from_markdown(original, "Improved body")

    assert rewritten.title == "Tool Review"
    assert rewritten.body == "Improved body"
