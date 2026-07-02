from __future__ import annotations

from dataclasses import dataclass
import re

from app.voice_profile import VoiceReview, review_voice


QUALITY_THRESHOLDS = {
    "voice_score": 7.5,
    "overall_score": 7.0,
}


@dataclass(frozen=True)
class QualityCheck:
    name: str
    passed: bool
    detail: str
    recommendation: str


@dataclass(frozen=True)
class QualityGateReport:
    surface: str
    overall_score: float
    ready_to_publish: bool
    voice_review: VoiceReview
    checks: list[QualityCheck]

    @property
    def passed_checks(self) -> int:
        return sum(1 for check in self.checks if check.passed)

    @property
    def failed_checks(self) -> int:
        return len(self.checks) - self.passed_checks

    def render(self) -> str:
        status = "Ready" if self.ready_to_publish else "Needs revision"
        lines = [
            "# Quality Gate Report",
            "",
            f"Surface: {self.surface}",
            f"Overall score: {self.overall_score:.1f}/10",
            f"Status: {status}",
            f"Voice score: {self.voice_review.score:.1f}/10",
            "",
            "## Checks",
        ]
        for check in self.checks:
            marker = "PASS" if check.passed else "FIX"
            lines.extend(
                [
                    f"### {marker}: {check.name}",
                    check.detail,
                    f"Recommendation: {check.recommendation}",
                    "",
                ]
            )
        lines.extend(["## Voice Review", self.voice_review.render()])
        return "\n".join(lines).strip()


def run_quality_gate(text: str, surface: str = "general") -> QualityGateReport:
    clean_text = text.strip()
    voice = review_voice(clean_text, surface=surface)
    checks = [
        _check_not_empty(clean_text),
        _check_voice_score(voice),
        _check_practical_anchor(clean_text),
        _check_tradeoff_or_failure(clean_text),
        _check_structure(clean_text),
        _check_call_to_action(clean_text),
        _check_generic_hype(voice),
    ]
    passed = sum(1 for check in checks if check.passed)
    check_score = (passed / len(checks)) * 10 if checks else 0.0
    overall_score = round((voice.score * 0.4) + (check_score * 0.6), 1)
    ready = bool(clean_text) and overall_score >= QUALITY_THRESHOLDS["overall_score"] and voice.score >= QUALITY_THRESHOLDS["voice_score"] and passed >= 5
    return QualityGateReport(
        surface=voice.surface,
        overall_score=overall_score,
        ready_to_publish=ready,
        voice_review=voice,
        checks=checks,
    )


def quality_rows(report: QualityGateReport) -> list[dict[str, object]]:
    return [
        {
            "check": check.name,
            "passed": check.passed,
            "detail": check.detail,
            "recommendation": check.recommendation,
        }
        for check in report.checks
    ]


def _check_not_empty(text: str) -> QualityCheck:
    passed = bool(text.strip())
    return QualityCheck(
        name="Draft exists",
        passed=passed,
        detail="Draft text is available." if passed else "No draft text was provided.",
        recommendation="Add a draft before running the quality gate." if not passed else "Keep going.",
    )


def _check_voice_score(voice: VoiceReview) -> QualityCheck:
    passed = voice.score >= QUALITY_THRESHOLDS["voice_score"]
    return QualityCheck(
        name="Praveen voice score",
        passed=passed,
        detail=f"Voice score is {voice.score:.1f}/10.",
        recommendation="Improve practical tone, remove hype, and add a builder-led anchor." if not passed else "Voice is strong enough for this stage.",
    )


def _check_practical_anchor(text: str) -> QualityCheck:
    lowered = text.lower()
    markers = ("workflow", "practical", "real", "example", "teaching", "debug", "builder", "trainer")
    passed = any(marker in lowered for marker in markers)
    return QualityCheck(
        name="Practical anchor",
        passed=passed,
        detail="Draft has practical/builder language." if passed else "Draft does not yet feel anchored in a real workflow.",
        recommendation="Add one concrete workflow, teaching, debugging, or builder example." if not passed else "Keep the practical anchor visible.",
    )


def _check_tradeoff_or_failure(text: str) -> QualityCheck:
    lowered = text.lower()
    markers = ("trade-off", "tradeoff", "failure", "mistake", "risk", "constraint", "cost")
    passed = any(marker in lowered for marker in markers)
    return QualityCheck(
        name="Trade-off or failure mode",
        passed=passed,
        detail="Draft includes a trade-off, mistake, risk, or failure mode." if passed else "No trade-off or failure mode is visible.",
        recommendation="Add one honest trade-off, mistake, risk, or failure mode." if not passed else "Good: this avoids generic positivity.",
    )


def _check_structure(text: str) -> QualityCheck:
    has_heading = bool(re.search(r"^#{1,3}\s+", text, flags=re.MULTILINE))
    paragraphs = [part for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    passed = has_heading or len(paragraphs) >= 3
    return QualityCheck(
        name="Readable structure",
        passed=passed,
        detail="Draft has headings or multiple readable blocks." if passed else "Draft may be too flat or unstructured.",
        recommendation="Add short paragraphs or headings for skimmability." if not passed else "Structure is readable enough.",
    )


def _check_call_to_action(text: str) -> QualityCheck:
    lowered = text.lower()
    markers = ("try", "ask", "start", "pick", "use", "share", "build", "write", "apply", "next")
    last_80_words = " ".join(text.split()[-80:]).lower()
    passed = any(marker in last_80_words for marker in markers) or any(f"{marker} " in lowered for marker in markers)
    return QualityCheck(
        name="Actionable close",
        passed=passed,
        detail="Draft includes an action-oriented ending or instruction." if passed else "Draft does not clearly tell the reader what to do next.",
        recommendation="End with one concrete next action." if not passed else "The close gives the reader something to do.",
    )


def _check_generic_hype(voice: VoiceReview) -> QualityCheck:
    has_hype_issue = any("generic ai phrases" in issue.lower() for issue in voice.issues)
    return QualityCheck(
        name="No generic AI hype",
        passed=not has_hype_issue,
        detail="No generic AI-hype phrase was detected." if not has_hype_issue else "Generic AI-hype phrasing was detected.",
        recommendation="Replace hype with concrete context, example, or trade-off." if has_hype_issue else "Keep the draft grounded.",
    )
