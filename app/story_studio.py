from __future__ import annotations

from dataclasses import dataclass

from app.idea_lab import IdeaLabReport


ALLOWED_STORY_FORMATS = {"chapter", "scene", "case_study", "dialogue"}
ALLOWED_STORY_TONES = {"practical", "dramatic", "mentor", "reflective"}


@dataclass(frozen=True)
class StoryCharacter:
    name: str
    role: str
    motivation: str
    flaw: str

    def render(self) -> str:
        return f"- **{self.name}** — {self.role}. Motivation: {self.motivation}. Flaw: {self.flaw}"


@dataclass(frozen=True)
class StoryScene:
    title: str
    purpose: str
    beats: list[str]

    def render(self) -> str:
        lines = [f"### {self.title}", "", self.purpose]
        lines.extend(f"- {beat}" for beat in self.beats)
        return "\n".join(lines).strip()


@dataclass(frozen=True)
class StoryDraft:
    signal_id: int
    source: str
    title: str
    format: str
    tone: str
    premise: str
    lesson: str
    characters: list[StoryCharacter]
    scenes: list[StoryScene]
    opening_hook: str
    closing_reflection: str
    reuse_notes: list[str]
    quality_checklist: list[str]

    def render(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"Format: {self.format}",
            f"Tone: {self.tone}",
            f"Signal ID: {self.signal_id}",
            f"Source: {self.source}",
            "",
            "## Premise",
            self.premise,
            "",
            "## Lesson",
            self.lesson,
            "",
            "## Characters",
        ]
        lines.extend(character.render() for character in self.characters)
        lines.extend(["", "## Opening Hook", self.opening_hook, "", "## Scenes"])
        lines.extend(scene.render() for scene in self.scenes)
        lines.extend(["", "## Closing Reflection", self.closing_reflection, "", "## Reuse Notes"])
        lines.extend(f"- {note}" for note in self.reuse_notes)
        lines.extend(["", "## Quality Checklist"])
        lines.extend(f"- [ ] {item}" for item in self.quality_checklist)
        return "\n".join(lines).strip()


def normalize_story_format(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_STORY_FORMATS:
        allowed = ", ".join(sorted(ALLOWED_STORY_FORMATS))
        raise ValueError(f"Unsupported story format '{value}'. Allowed formats: {allowed}")
    return normalized


def normalize_story_tone(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_STORY_TONES:
        allowed = ", ".join(sorted(ALLOWED_STORY_TONES))
        raise ValueError(f"Unsupported story tone '{value}'. Allowed tones: {allowed}")
    return normalized


def generate_story(report: IdeaLabReport, story_format: str = "chapter", tone: str = "practical") -> StoryDraft:
    format_name = normalize_story_format(story_format)
    tone_name = normalize_story_tone(tone)
    return StoryDraft(
        signal_id=report.signal_id,
        source=report.source,
        title=_title(report, format_name),
        format=format_name,
        tone=tone_name,
        premise=_premise(report),
        lesson=_lesson(report),
        characters=_characters(tone_name),
        scenes=_scenes(report, format_name),
        opening_hook=_opening_hook(report, tone_name),
        closing_reflection=_closing_reflection(report),
        reuse_notes=_reuse_notes(format_name),
        quality_checklist=_quality_checklist(format_name, tone_name),
    )


def _title(report: IdeaLabReport, story_format: str) -> str:
    if story_format == "case_study":
        return f"Case Study: The Team That Misread a {report.category} Signal"
    if story_format == "dialogue":
        return f"Dialogue: Turning One {report.category} Signal Into Judgment"
    if story_format == "scene":
        return "Scene: The Signal Nobody Converted"
    return f"Story Chapter: The Team That Learned {report.category} the Hard Way"


def _premise(report: IdeaLabReport) -> str:
    return f"A small technical team finds a signal from {report.source} but must turn it into a framework before it becomes useful."


def _lesson(report: IdeaLabReport) -> str:
    return f"Technical lesson: {report.core_insight} Human lesson: saved information matters only when it changes behavior."


def _characters(tone: str) -> list[StoryCharacter]:
    mentor_name = "Mira" if tone == "mentor" else "Asha"
    return [
        StoryCharacter(mentor_name, "Senior engineer", "Turn information into decisions.", "Assumes the pattern is obvious."),
        StoryCharacter("Ravi", "Builder", "Move fast without missing trends.", "Saves links instead of extracting lessons."),
        StoryCharacter("Naina", "Product thinker", "Make ideas useful for readers and learners.", "Pushes for output too early."),
    ]


def _scenes(report: IdeaLabReport, story_format: str) -> list[StoryScene]:
    scenes = [
        StoryScene(
            "The saved signal",
            "Introduce the team and the raw signal.",
            [f"Ravi shares a signal from {report.source}.", "The team is interested but unclear on the next step.", report.core_insight],
        ),
        StoryScene(
            "The hidden gap",
            "Show what shallow reading misses.",
            [report.hidden_gap, "The first draft sounds generic.", "The team searches for a sharper reader problem."],
        ),
        StoryScene(
            "The better frame",
            "Turn the signal into a reusable method.",
            [report.novel_angle, "The team maps signal to insight, gap, artifact, and queue.", "Each person chooses one useful output."],
        ),
        StoryScene(
            "The changed habit",
            "End with a new operating rhythm.",
            ["The team stops only saving links.", "They convert the best signal into an action.", "The final lesson becomes a checklist."],
        ),
    ]
    if story_format == "scene":
        return scenes[:2]
    if story_format == "dialogue":
        return scenes[:3]
    return scenes


def _opening_hook(report: IdeaLabReport, tone: str) -> str:
    if tone == "mentor":
        return "Mira opened the saved signal and asked one question: what will this change?"
    if tone == "reflective":
        return "At the end of the week, the team found its best insight sitting unused in a saved message."
    if tone == "dramatic":
        return f"The team had five saved signals and no shared understanding of {report.category}."
    return "The signal looked useful. That was the problem: everyone saved it, but nobody converted it."


def _closing_reflection(report: IdeaLabReport) -> str:
    return f"The team learned that {report.category} signals become useful only after someone extracts a lesson and turns it into a reusable artifact."


def _reuse_notes(story_format: str) -> list[str]:
    return [
        "Use the opening hook as a LinkedIn intro.",
        "Turn each scene into a podcast segment.",
        "Reuse the hidden gap as a teaching prompt.",
        "Convert the final lesson into a creator checklist.",
        f"Track this as a {story_format} item in the Publishing Queue.",
    ]


def _quality_checklist(story_format: str, tone: str) -> list[str]:
    return [
        "The story teaches a technical lesson without sounding generic.",
        "The characters have motivation and flaws.",
        "There is a visible conflict caused by shallow interpretation.",
        "The story resolves with a changed habit or decision model.",
        f"The output works as a {story_format} with a {tone} tone.",
    ]
