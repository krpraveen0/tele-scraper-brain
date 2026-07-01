from __future__ import annotations

from app.blueprint_generator import ALLOWED_BLUEPRINT_TYPES, Blueprint, generate_blueprint
from app.idea_lab import generate_idea_lab_report
from app.storage import SignalStore


def create_blueprint(store: SignalStore, signal_id: int, blueprint_type: str) -> Blueprint:
    signal = store.get_signal(signal_id)
    if signal is None:
        raise ValueError(f"Signal id {signal_id} does not exist.")
    report = generate_idea_lab_report(signal)
    return generate_blueprint(report, blueprint_type)


def allowed_blueprint_types() -> list[str]:
    return sorted(ALLOWED_BLUEPRINT_TYPES)
