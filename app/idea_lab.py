from __future__ import annotations

from dataclasses import dataclass
from textwrap import shorten

from app.models import StoredSignal


ANGLE_TYPES = (
    "beginner",
    "senior_engineer",
    "architect",
    "founder_product",
    "teaching",
    "career",
    "contrarian",
    "podcast",
    "storybook",
    "course",
)


@dataclass(frozen=True)
class ContentAngle:
    angle_type: str
    title: str
    target_audience: str
    description: str

    def render(self) -> str:
        label = self.angle_type.replace("_", " ").title()
        return f"- **{label}: {self.title}**\n  - Audience: {self.target_audience}\n  - {self.description}"


@dataclass(frozen=True)
class IdeaSeed:
    seed_type: str
    title: str
    outline: list[str]

    def render(self) -> str:
        lines = [f"### {self.seed_type.replace('_', ' ').title()}: {self.title}"]
        lines.extend(f"- {item}" for item in self.outline)
        return "\n".join(lines)


@dataclass(frozen=True)
class IdeaLabReport:
    signal_id: int
    source: str
    category: str
    core_insight: str
    hidden_gap: str
    novel_angle: str
    recommended_format: str
    content_angles: list[ContentAngle]
    title_ideas: list[str]
    diagram_ideas: list[str]
    seeds: list[IdeaSeed]
    quality_checklist: list[str]

    def render(self) -> str:
        lines = [
            f"# Idea Lab Report — Signal {self.signal_id}",
            "",
            f"Source: {self.source}",
            f"Category: {self.category}",
            f"Recommended format: {self.recommended_format}",
            "",
            "## Core Insight",
            self.core_insight,
            "",
            "## Hidden Gap",
            self.hidden_gap,
            "",
            "## Novel Angle",
            self.novel_angle,
            "",
            "## Content Angles",
        ]
        lines.extend(angle.render() for angle in self.content_angles)
        lines.extend(["", "## Title Ideas"])
        lines.extend(f"- {title}" for title in self.title_ideas)
        lines.extend(["", "## Diagram Ideas"])
        lines.extend(f"- {idea}" for idea in self.diagram_ideas)
        lines.extend(["", "## Content Seeds"])
        lines.extend(seed.render() for seed in self.seeds)
        lines.extend(["", "## Quality Checklist"])
        lines.extend(f"- [ ] {item}" for item in self.quality_checklist)
        return "\n".join(lines).strip()


def generate_idea_lab_report(signal: StoredSignal) -> IdeaLabReport:
    summary = _summary(signal)
    topic = _topic(signal)
    category = signal.analysis.category
    source = signal.source_title

    core_insight = (
        f"This signal is about {topic}. The practical insight is that {category.lower()} value comes from "
        "turning the raw update into a decision, example, framework, or teaching artifact."
    )
    hidden_gap = (
        "Most people would save this as another link or headline. The hidden gap is converting it into reusable "
        "judgment: what to learn, what to build, what to teach, and what to ignore."
    )
    novel_angle = (
        f"Use the signal from {source} as a seed for a personal creator workflow: one technical signal can become "
        "a blog angle, course module, podcast scene, and story chapter if it is framed through a clear reader problem."
    )

    return IdeaLabReport(
        signal_id=signal.id,
        source=source,
        category=category,
        core_insight=core_insight,
        hidden_gap=hidden_gap,
        novel_angle=novel_angle,
        recommended_format=_recommended_format(signal),
        content_angles=_content_angles(topic, category, summary),
        title_ideas=_title_ideas(topic, category),
        diagram_ideas=_diagram_ideas(topic, category),
        seeds=_idea_seeds(topic, category, summary),
        quality_checklist=_quality_checklist(),
    )


def _summary(signal: StoredSignal) -> str:
    text = signal.analysis.summary or signal.analysis.reason or signal.message_text
    return shorten(" ".join(text.split()), width=220, placeholder="...")


def _topic(signal: StoredSignal) -> str:
    if signal.analysis.tags:
        return ", ".join(tag.lstrip("#") for tag in signal.analysis.tags[:3])
    return signal.analysis.category.lower()


def _recommended_format(signal: StoredSignal) -> str:
    action = signal.analysis.suggested_action.lower()
    category = signal.analysis.category
    if "linkedin" in action:
        return "LinkedIn post"
    if "medium" in action:
        return "Medium article blueprint"
    if "class" in action or category == "Teaching":
        return "Course module"
    if category == "Career":
        return "Career note"
    if category == "English":
        return "Speaking practice script"
    if category == "Research":
        return "Research article outline"
    if category == "Tools":
        return "Tool review"
    return "Tech blog blueprint"


def _content_angles(topic: str, category: str, summary: str) -> list[ContentAngle]:
    templates = {
        "beginner": (
            "Explain the signal without jargon",
            "Beginners and students",
            f"Use {topic} to explain the core idea in simple language, then connect it to one practical example.",
        ),
        "senior_engineer": (
            "What an experienced engineer should notice",
            "Senior software and AI engineers",
            f"Extract the trade-offs, failure modes, and production implications behind this signal: {summary}",
        ),
        "architect": (
            "Turn the signal into an architecture decision",
            "Architects and technical leads",
            f"Frame {topic} as a design decision involving routing, memory, evaluation, cost, reliability, or observability.",
        ),
        "founder_product": (
            "Why this matters as a product bet",
            "Founders and product thinkers",
            f"Connect {category.lower()} to user pain, adoption friction, workflow value, and defensibility.",
        ),
        "teaching": (
            "Teach this with a classroom demo",
            "Trainers and learners",
            f"Convert the signal into a lesson with analogy, demo, hands-on task, and discussion question.",
        ),
        "career": (
            "Convert the signal into career leverage",
            "Engineers planning career growth",
            f"Identify skills, keywords, portfolio proof, and interview stories suggested by {topic}.",
        ),
        "contrarian": (
            "What most people may be getting wrong",
            "Opinionated technical readers",
            "Challenge the obvious interpretation and show a sharper, more practical way to think about the signal.",
        ),
        "podcast": (
            "Turn it into a spoken episode",
            "Podcast listeners and technical storytellers",
            f"Open with a real work scene, introduce the conflict, then explain the technical lesson behind {topic}.",
        ),
        "storybook": (
            "Turn it into a tech firm story chapter",
            "Readers who enjoy narrative learning",
            "Create a team, a failed decision, a debugging moment, and a lesson that makes the concept memorable.",
        ),
        "course": (
            "Turn it into a structured course module",
            "Students and workshop participants",
            f"Build a module around {topic} with objectives, examples, exercises, assessment, and trainer notes.",
        ),
    }
    return [ContentAngle(angle_type=key, title=value[0], target_audience=value[1], description=value[2]) for key, value in templates.items()]


def _title_ideas(topic: str, category: str) -> list[str]:
    clean_topic = topic.title()
    return [
        f"Your Next {category} Idea Is Hiding Inside One Signal",
        f"How to Turn {clean_topic} Into Practical Engineering Judgment",
        f"Stop Saving Links. Start Extracting Systems.",
        f"The Signal-to-Blueprint Method for Technical Creators",
        f"What {clean_topic} Teaches Us About Building Better AI Workflows",
    ]


def _diagram_ideas(topic: str, category: str) -> list[str]:
    return [
        "Signal -> Insight -> Angle -> Blueprint -> Draft flow diagram",
        f"{category} decision tree: read, build, teach, write, or archive",
        f"One {topic} signal branching into blog, course, podcast, and story outputs",
        "Quality gate checklist: originality, usefulness, depth, story, reuse",
    ]


def _idea_seeds(topic: str, category: str, summary: str) -> list[IdeaSeed]:
    return [
        IdeaSeed(
            seed_type="blog_seed",
            title=f"The practical lesson inside {topic}",
            outline=[
                f"Open with the signal: {summary}",
                "Explain why the obvious interpretation is incomplete.",
                "Introduce a practical framework readers can apply.",
                "Close with a next action for builders.",
            ],
        ),
        IdeaSeed(
            seed_type="course_seed",
            title=f"Teach {topic} through a real signal",
            outline=[
                "Define the learning objective.",
                "Show the raw signal and ask what is useful versus noisy.",
                "Convert the signal into a small exercise or mini-project.",
                "End with assessment questions.",
            ],
        ),
        IdeaSeed(
            seed_type="podcast_seed",
            title=f"A conversation about {topic}",
            outline=[
                "Start with a workplace scene.",
                "Introduce a conflict or bad decision.",
                "Discuss the technical trade-off.",
                "End with the listener takeaway.",
            ],
        ),
        IdeaSeed(
            seed_type="storybook_seed",
            title=f"The team that misunderstood {category.lower()}",
            outline=[
                "Create a fictional team facing pressure.",
                "Show the mistake they make from shallow interpretation.",
                "Reveal the better framework.",
                "End with a memorable engineering lesson.",
            ],
        ),
    ]


def _quality_checklist() -> list[str]:
    return [
        "The idea has a non-obvious angle.",
        "The reader pain is clear.",
        "The output includes a practical example or framework.",
        "The technical trade-off is visible.",
        "The story has tension or a before/after transformation.",
        "The idea can be reused as a blog, course, podcast, or story chapter.",
    ]
