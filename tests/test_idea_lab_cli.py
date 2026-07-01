from __future__ import annotations

from types import SimpleNamespace

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


def test_parse_args_accepts_idea_lab_command(monkeypatch) -> None:
    from app import main as cli

    monkeypatch.setattr("sys.argv", ["prog", "idea-lab", "--id", "42"])

    args = cli.parse_args()

    assert args.command == "idea-lab"
    assert args.id == 42


def test_run_idea_lab_prints_report(monkeypatch) -> None:
    from app import main as cli

    class FakeStore:
        def __init__(self, database_path: str) -> None:
            assert database_path == "fake.db"

        def get_signal(self, signal_id: int) -> StoredSignal | None:
            return make_stored_signal() if signal_id == 42 else None

    printed: list[str] = []
    monkeypatch.setattr(cli, "load_settings", lambda: SimpleNamespace(database_path="fake.db"))
    monkeypatch.setattr(cli, "SignalStore", FakeStore)
    monkeypatch.setattr(cli, "console", SimpleNamespace(print=lambda value: printed.append(str(value))))

    cli.run_idea_lab(42)

    assert printed
    assert "# Idea Lab Report" in printed[0]
    assert "## Content Angles" in printed[0]
    assert "## Quality Checklist" in printed[0]


def test_run_idea_lab_rejects_missing_signal(monkeypatch) -> None:
    from app import main as cli

    class FakeStore:
        def __init__(self, database_path: str) -> None:
            assert database_path == "fake.db"

        def get_signal(self, signal_id: int) -> None:
            return None

    monkeypatch.setattr(cli, "load_settings", lambda: SimpleNamespace(database_path="fake.db"))
    monkeypatch.setattr(cli, "SignalStore", FakeStore)

    try:
        cli.run_idea_lab(999)
    except ValueError as exc:
        assert "Signal id 999 does not exist" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing signal")
