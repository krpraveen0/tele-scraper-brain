from __future__ import annotations

from dataclasses import dataclass

from app.idea_lab import IdeaLabReport


ALLOWED_COURSE_LEVELS = {"beginner", "intermediate", "advanced"}
ALLOWED_COURSE_FORMATS = {"workshop", "lesson", "mini_project", "assessment"}


@dataclass(frozen=True)
class CourseActivity:
    title: str
    duration_minutes: int
    instructions: list[str]
    expected_output: str

    def render(self) -> str:
        lines = [f"### Activity: {self.title}", "", f"Duration: {self.duration_minutes} minutes", "", "Instructions:"]
        lines.extend(f"- {step}" for step in self.instructions)
        lines.extend(["", f"Expected output: {self.expected_output}"])
        return "\n".join(lines).strip()


@dataclass(frozen=True)
class AssessmentQuestion:
    question: str
    expected_answer: str

    def render(self) -> str:
        return f"- **Question:** {self.question}\n  - Expected answer: {self.expected_answer}"


@dataclass(frozen=True)
class CourseModule:
    signal_id: int
    source: str
    title: str
    level: str
    format: str
    target_learners: str
    learning_outcome: str
    prerequisites: list[str]
    concept_explanation: str
    analogy: str
    demo_steps: list[str]
    activities: list[CourseActivity]
    common_mistakes: list[str]
    assessment: list[AssessmentQuestion]
    trainer_notes: list[str]
    extension_tasks: list[str]

    def render(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"Level: {self.level}",
            f"Format: {self.format}",
            f"Signal ID: {self.signal_id}",
            f"Source: {self.source}",
            "",
            "## Target Learners",
            self.target_learners,
            "",
            "## Learning Outcome",
            self.learning_outcome,
            "",
            "## Prerequisites",
        ]
        lines.extend(f"- {item}" for item in self.prerequisites)
        lines.extend(["", "## Concept Explanation", self.concept_explanation, "", "## Analogy", self.analogy, "", "## Demo Steps"])
        lines.extend(f"- {step}" for step in self.demo_steps)
        lines.extend(["", "## Activities"])
        lines.extend(activity.render() for activity in self.activities)
        lines.extend(["", "## Common Mistakes"])
        lines.extend(f"- {item}" for item in self.common_mistakes)
        lines.extend(["", "## Assessment"])
        lines.extend(question.render() for question in self.assessment)
        lines.extend(["", "## Trainer Notes"])
        lines.extend(f"- {note}" for note in self.trainer_notes)
        lines.extend(["", "## Extension Tasks"])
        lines.extend(f"- {task}" for task in self.extension_tasks)
        return "\n".join(lines).strip()


def normalize_course_level(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_COURSE_LEVELS:
        allowed = ", ".join(sorted(ALLOWED_COURSE_LEVELS))
        raise ValueError(f"Unsupported course level '{value}'. Allowed levels: {allowed}")
    return normalized


def normalize_course_format(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_COURSE_FORMATS:
        allowed = ", ".join(sorted(ALLOWED_COURSE_FORMATS))
        raise ValueError(f"Unsupported course format '{value}'. Allowed formats: {allowed}")
    return normalized


def generate_course_module(report: IdeaLabReport, level: str = "intermediate", course_format: str = "workshop") -> CourseModule:
    normalized_level = normalize_course_level(level)
    normalized_format = normalize_course_format(course_format)
    topic = _topic(report)

    return CourseModule(
        signal_id=report.signal_id,
        source=report.source,
        title=f"Course Module: Turn {report.category} Signals Into Practical Artifacts",
        level=normalized_level,
        format=normalized_format,
        target_learners=_target_learners(normalized_level),
        learning_outcome=f"Learners will inspect one real signal about {topic}, extract the hidden gap, and convert it into a usable technical artifact.",
        prerequisites=_prerequisites(normalized_level),
        concept_explanation=_concept_explanation(report),
        analogy="Treat a saved signal like raw ore: it becomes valuable only after extraction, refinement, shaping, and use.",
        demo_steps=_demo_steps(report),
        activities=_activities(report, normalized_format),
        common_mistakes=_common_mistakes(),
        assessment=_assessment(report),
        trainer_notes=_trainer_notes(normalized_level),
        extension_tasks=_extension_tasks(report),
    )


def _topic(report: IdeaLabReport) -> str:
    if report.title_ideas:
        return report.title_ideas[0]
    return report.category


def _target_learners(level: str) -> str:
    if level == "beginner":
        return "Students and early-career developers learning how to convert information into useful technical thinking."
    if level == "advanced":
        return "Senior engineers, architects, and trainers who want to teach signal extraction as a repeatable system."
    return "Developers, AI engineers, and trainers who know the basics and want a practical creator workflow."


def _prerequisites(level: str) -> list[str]:
    base = ["Ability to read a short technical signal or article summary.", "Basic familiarity with technical writing or learning notes."]
    if level == "advanced":
        return base + ["Experience comparing architecture, workflow, or product trade-offs."]
    if level == "beginner":
        return ["Curiosity about technical topics.", "Willingness to write short observations in plain English."]
    return base + ["Some experience building, teaching, or explaining technical concepts."]


def _concept_explanation(report: IdeaLabReport) -> str:
    return (
        f"The source signal says: {report.core_insight} The teaching opportunity is the gap: {report.hidden_gap} "
        f"The course should help learners move from passive reading to active extraction using this angle: {report.novel_angle}"
    )


def _demo_steps(report: IdeaLabReport) -> list[str]:
    return [
        f"Show the source and category: {report.source} / {report.category}.",
        "Ask learners what they would normally do with this signal.",
        "Highlight the core insight in one sentence.",
        "Identify the hidden gap or non-obvious lesson.",
        "Turn the signal into one artifact: blog idea, teaching example, podcast scene, story chapter, or checklist.",
    ]


def _activities(report: IdeaLabReport, course_format: str) -> list[CourseActivity]:
    primary = CourseActivity(
        title="Signal Extraction Drill",
        duration_minutes=20,
        instructions=[
            "Read the signal summary.",
            "Write the core insight in one sentence.",
            "Write the hidden gap in one sentence.",
            "Choose one target audience.",
            "Draft one practical artifact idea.",
        ],
        expected_output="A one-page signal extraction worksheet.",
    )
    second = CourseActivity(
        title="Artifact Conversion Task",
        duration_minutes=30,
        instructions=[
            "Pick one angle from the Idea Lab report.",
            "Convert it into a 5-point outline.",
            "Add one example, one mistake, and one next action.",
            "Pair-review the outline for usefulness and originality.",
        ],
        expected_output="A reusable outline for a blog, lesson, podcast, or story asset.",
    )
    project = CourseActivity(
        title="Mini Project: Build a Signal-to-Blueprint Board",
        duration_minutes=45,
        instructions=[
            "Collect three saved signals.",
            "Score each signal for usefulness and originality.",
            "Create one blueprint from the strongest signal.",
            "Add the blueprint to a future publishing or teaching queue.",
        ],
        expected_output="A simple creator board with signals, insights, angles, and next actions.",
    )
    if course_format == "mini_project":
        return [primary, second, project]
    if course_format == "assessment":
        return [primary]
    return [primary, second]


def _common_mistakes() -> list[str]:
    return [
        "Copying the signal instead of extracting a personal insight.",
        "Writing a generic summary without a reader problem.",
        "Skipping examples and trade-offs.",
        "Trying to create a full draft before creating a clear blueprint.",
        "Confusing more information with better judgment.",
    ]


def _assessment(report: IdeaLabReport) -> list[AssessmentQuestion]:
    return [
        AssessmentQuestion(
            question="What is the core insight of the signal?",
            expected_answer=report.core_insight,
        ),
        AssessmentQuestion(
            question="What hidden gap makes this signal useful for creators or engineers?",
            expected_answer=report.hidden_gap,
        ),
        AssessmentQuestion(
            question="What artifact can you create from this signal?",
            expected_answer="A blog outline, course lesson, podcast scene, story chapter, checklist, or implementation note.",
        ),
        AssessmentQuestion(
            question="How do you know the artifact is not generic?",
            expected_answer="It has a clear audience, a non-obvious angle, a practical example, and a concrete next action.",
        ),
    ]


def _trainer_notes(level: str) -> list[str]:
    notes = [
        "Keep learners focused on one signal at a time.",
        "Ask for short sentences before long explanations.",
        "Push learners to name the audience before writing the artifact.",
        "Use peer review to check whether the output is useful or generic.",
    ]
    if level == "beginner":
        notes.append("Help learners simplify jargon before asking for originality.")
    if level == "advanced":
        notes.append("Ask learners to include trade-offs, failure modes, and system impact.")
    return notes


def _extension_tasks(report: IdeaLabReport) -> list[str]:
    return [
        "Turn the worksheet into a LinkedIn post.",
        "Turn the artifact outline into a Medium article blueprint.",
        "Create a classroom demo using the same signal.",
        "Create a podcast opening scene from the hidden gap.",
        f"Build a follow-up lesson around {report.category} decision-making.",
    ]
