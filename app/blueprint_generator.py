from __future__ import annotations

from dataclasses import dataclass

from app.idea_lab import IdeaLabReport


ALLOWED_BLUEPRINT_TYPES = {
    "tech_blog",
    "deep_article",
    "course_module",
    "podcast_script",
    "storybook_chapter",
}


@dataclass(frozen=True)
class BlueprintSection:
    title: str
    purpose: str
    bullets: list[str]

    def render(self) -> str:
        lines = [f"### {self.title}", "", self.purpose]
        if self.bullets:
            lines.append("")
            lines.extend(f"- {bullet}" for bullet in self.bullets)
        return "\n".join(lines).strip()


@dataclass(frozen=True)
class Blueprint:
    signal_id: int
    source: str
    blueprint_type: str
    title: str
    audience: str
    promise: str
    opening_scene: str
    unique_angle: str
    framework: str
    sections: list[BlueprintSection]
    diagram_idea: str
    conclusion: str
    call_to_action: str
    quality_checklist: list[str]

    def render(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"Blueprint type: {self.blueprint_type}",
            f"Signal ID: {self.signal_id}",
            f"Source: {self.source}",
            "",
            "## Audience",
            self.audience,
            "",
            "## Promise",
            self.promise,
            "",
            "## Opening Scene",
            self.opening_scene,
            "",
            "## Unique Angle",
            self.unique_angle,
            "",
            "## Framework",
            self.framework,
            "",
            "## Structure",
        ]
        lines.extend(section.render() for section in self.sections)
        lines.extend(
            [
                "",
                "## Diagram Idea",
                self.diagram_idea,
                "",
                "## Conclusion",
                self.conclusion,
                "",
                "## Call To Action",
                self.call_to_action,
                "",
                "## Quality Checklist",
            ]
        )
        lines.extend(f"- [ ] {item}" for item in self.quality_checklist)
        return "\n".join(lines).strip()


def normalize_blueprint_type(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_BLUEPRINT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_BLUEPRINT_TYPES))
        raise ValueError(f"Unsupported blueprint type '{value}'. Allowed blueprint types: {allowed}")
    return normalized


def generate_blueprint(report: IdeaLabReport, blueprint_type: str) -> Blueprint:
    normalized_type = normalize_blueprint_type(blueprint_type)
    builders = {
        "tech_blog": _tech_blog_blueprint,
        "deep_article": _deep_article_blueprint,
        "course_module": _course_module_blueprint,
        "podcast_script": _podcast_script_blueprint,
        "storybook_chapter": _storybook_chapter_blueprint,
    }
    return builders[normalized_type](report)


def _base_quality_checklist() -> list[str]:
    return [
        "The reader pain is explicit in the first third.",
        "The unique angle is not a generic AI-generated summary.",
        "The structure includes a practical example or framework.",
        "At least one trade-off or failure mode is visible.",
        "The output can be reused as a blog, course, podcast, or story asset.",
    ]


def _primary_title(report: IdeaLabReport, fallback: str) -> str:
    return report.title_ideas[0] if report.title_ideas else fallback


def _primary_diagram(report: IdeaLabReport, fallback: str) -> str:
    return report.diagram_ideas[0] if report.diagram_ideas else fallback


def _tech_blog_blueprint(report: IdeaLabReport) -> Blueprint:
    return Blueprint(
        signal_id=report.signal_id,
        source=report.source,
        blueprint_type="tech_blog",
        title=_primary_title(report, "A Practical Technical Lesson From One Signal"),
        audience="Software engineers, AI engineers, and technical builders who want practical takeaways without hype.",
        promise="By the end, the reader should understand the signal, see the hidden gap, and apply one practical framework.",
        opening_scene="A builder saves another useful link, but nothing changes until the signal becomes a decision, example, or workflow.",
        unique_angle=report.novel_angle,
        framework="Signal -> Insight -> Gap -> Practical Framework -> Next Action",
        sections=[
            BlueprintSection(
                title="The signal",
                purpose="Introduce the saved signal and why it deserves attention.",
                bullets=[report.core_insight, f"Source context: {report.source}"],
            ),
            BlueprintSection(
                title="The hidden gap",
                purpose="Show why the common interpretation is incomplete.",
                bullets=[report.hidden_gap, "Explain what most readers may miss."],
            ),
            BlueprintSection(
                title="The practical framework",
                purpose="Convert the signal into a reusable engineering pattern.",
                bullets=["Define the framework.", "Show when to use it.", "Show when not to use it."],
            ),
            BlueprintSection(
                title="Example and trade-offs",
                purpose="Make the idea usable through a concrete example.",
                bullets=["Add one implementation or workflow example.", "Name one failure mode.", "Name one cost, quality, or reliability trade-off."],
            ),
        ],
        diagram_idea=_primary_diagram(report, "Signal to blueprint flow diagram"),
        conclusion="The signal matters only when it changes how the reader thinks, builds, teaches, or decides.",
        call_to_action="Pick one signal from your own workflow and convert it into a framework before saving another link.",
        quality_checklist=_base_quality_checklist(),
    )


def _deep_article_blueprint(report: IdeaLabReport) -> Blueprint:
    return Blueprint(
        signal_id=report.signal_id,
        source=report.source,
        blueprint_type="deep_article",
        title=f"Deep Dive: {_primary_title(report, report.category)}",
        audience="Senior engineers, architects, and technical readers who want context, trade-offs, and implementation depth.",
        promise="By the end, the reader should understand the broader system implications behind the signal.",
        opening_scene="A team reacts to a new technical signal as news, but the deeper value is in the design pressure it reveals.",
        unique_angle=report.novel_angle,
        framework="Context -> System Pressure -> Design Options -> Trade-offs -> Operating Model",
        sections=[
            BlueprintSection(
                title="Context and why now",
                purpose="Explain why this signal is timely and what changed in the ecosystem.",
                bullets=[report.core_insight, "Explain the larger trend or pressure behind it."],
            ),
            BlueprintSection(
                title="System-level problem",
                purpose="Move from headline to architecture, workflow, or organizational impact.",
                bullets=[report.hidden_gap, "Identify who feels the pain and why."],
            ),
            BlueprintSection(
                title="Design options",
                purpose="Compare multiple ways to respond to the signal.",
                bullets=["Option 1: simple workflow change.", "Option 2: architecture or tool change.", "Option 3: evaluation or governance change."],
            ),
            BlueprintSection(
                title="Trade-offs and failure modes",
                purpose="Show engineering judgment rather than only enthusiasm.",
                bullets=["Cost trade-off.", "Complexity trade-off.", "Quality or reliability failure mode."],
            ),
            BlueprintSection(
                title="Practical operating model",
                purpose="Close with a repeatable way to apply the insight.",
                bullets=["Checklist.", "Metrics to observe.", "Decision rule for teams."],
            ),
        ],
        diagram_idea="System pressure map: signal -> affected workflow -> design options -> trade-offs",
        conclusion="A deep article should leave readers with a better decision model, not just more information.",
        call_to_action="Use the decision model to evaluate one current AI engineering or teaching workflow.",
        quality_checklist=_base_quality_checklist()
        + ["The article includes multiple design options.", "The article includes at least two trade-offs."],
    )


def _course_module_blueprint(report: IdeaLabReport) -> Blueprint:
    return Blueprint(
        signal_id=report.signal_id,
        source=report.source,
        blueprint_type="course_module",
        title=f"Course Module: Turning {report.category} Signals Into Practical Work",
        audience="Students, junior engineers, and workshop participants who learn best through real examples.",
        promise="By the end, learners should be able to inspect a real signal and convert it into a useful technical artifact.",
        opening_scene="The instructor shows a real saved signal and asks learners to separate useful insight from noise.",
        unique_angle=report.novel_angle,
        framework="Observe -> Classify -> Extract -> Build -> Reflect",
        sections=[
            BlueprintSection(
                title="Learning outcome",
                purpose="Set the transformation for the learner.",
                bullets=["Learners can identify insight, gap, audience, and next action from one signal."],
            ),
            BlueprintSection(
                title="Concept explanation",
                purpose="Explain the idea in plain language before using tools.",
                bullets=[report.core_insight, report.hidden_gap],
            ),
            BlueprintSection(
                title="Demo",
                purpose="Model the process live with one signal.",
                bullets=["Show the raw signal.", "Highlight insight and gap.", "Convert it into a content or project seed."],
            ),
            BlueprintSection(
                title="Hands-on task",
                purpose="Make learners practice, not just listen.",
                bullets=["Give each learner one signal.", "Ask for one angle and one blueprint.", "Peer review for usefulness and originality."],
            ),
            BlueprintSection(
                title="Assessment",
                purpose="Check whether the learner can apply the method independently.",
                bullets=["What is the reader pain?", "What is the unique angle?", "What practical artifact can be created?"],
            ),
        ],
        diagram_idea="Classroom flow: raw signal -> insight -> gap -> artifact -> reflection",
        conclusion="A good course module turns one real-world signal into a repeatable learner skill.",
        call_to_action="Ask learners to bring one technical signal and convert it into a mini teaching artifact.",
        quality_checklist=_base_quality_checklist()
        + ["The module has a learning outcome.", "The module has a hands-on task.", "The module has assessment questions."],
    )


def _podcast_script_blueprint(report: IdeaLabReport) -> Blueprint:
    return Blueprint(
        signal_id=report.signal_id,
        source=report.source,
        blueprint_type="podcast_script",
        title=f"Podcast Script: {_primary_title(report, report.category)}",
        audience="Technical listeners who prefer story-led explanation and practical takeaways.",
        promise="By the end, the listener should remember the conflict, the decision, and the technical lesson.",
        opening_scene="Open with a short workplace moment where a team has too many signals and too little clarity.",
        unique_angle=report.novel_angle,
        framework="Scene -> Tension -> Explanation -> Trade-off -> Takeaway",
        sections=[
            BlueprintSection(
                title="Cold open",
                purpose="Start with a short scene that creates curiosity.",
                bullets=["Describe a team, deadline, or confusing signal.", "End with a question the episode will answer."],
            ),
            BlueprintSection(
                title="Signal explanation",
                purpose="Explain the signal in conversational language.",
                bullets=[report.core_insight, "Avoid jargon in the first explanation."],
            ),
            BlueprintSection(
                title="Conflict",
                purpose="Make the episode more than a summary.",
                bullets=[report.hidden_gap, "Show what goes wrong when the signal is misunderstood."],
            ),
            BlueprintSection(
                title="Practical lesson",
                purpose="Give the listener a framework they can reuse.",
                bullets=["Name the framework.", "Explain one trade-off.", "Give one action for this week."],
            ),
        ],
        diagram_idea="Episode arc: scene -> conflict -> framework -> takeaway",
        conclusion="The episode should end with one memorable sentence the listener can repeat.",
        call_to_action="Invite the listener to convert one saved signal into a short spoken explanation.",
        quality_checklist=_base_quality_checklist()
        + ["The script sounds readable aloud.", "The episode has a clear conflict and listener takeaway."],
    )


def _storybook_chapter_blueprint(report: IdeaLabReport) -> Blueprint:
    return Blueprint(
        signal_id=report.signal_id,
        source=report.source,
        blueprint_type="storybook_chapter",
        title=f"Storybook Chapter: The Team That Learned {report.category} the Hard Way",
        audience="Readers who enjoy learning technical ideas through fictional but realistic workplace stories.",
        promise="By the end, the reader should remember the technical lesson because they saw a team struggle through it.",
        opening_scene="A small tech team misreads a signal as a shortcut and creates a bigger problem for themselves.",
        unique_angle=report.novel_angle,
        framework="Character -> Context -> Conflict -> Decision -> Consequence -> Lesson",
        sections=[
            BlueprintSection(
                title="Characters and setting",
                purpose="Create a believable team and situation.",
                bullets=["Senior engineer.", "Junior engineer.", "Product pressure.", "A signal from the outside world."],
            ),
            BlueprintSection(
                title="The mistake",
                purpose="Show the shallow interpretation of the signal.",
                bullets=[report.hidden_gap, "The team saves or copies the idea without understanding the system impact."],
            ),
            BlueprintSection(
                title="The failure moment",
                purpose="Create tension and consequence.",
                bullets=["A workflow breaks.", "A decision becomes expensive.", "The team realizes the missing framework."],
            ),
            BlueprintSection(
                title="The better framework",
                purpose="Teach the technical lesson through resolution.",
                bullets=[report.core_insight, "The team turns the signal into a repeatable decision process."],
            ),
            BlueprintSection(
                title="The chapter lesson",
                purpose="End with a memorable takeaway.",
                bullets=["Better thinking beats more information.", "A signal is valuable only when converted into action."],
            ),
        ],
        diagram_idea="Story arc: character -> conflict -> failure -> framework -> lesson",
        conclusion="The chapter should make the technical principle emotionally memorable, not just technically correct.",
        call_to_action="Use the chapter as a teaching story before introducing the formal framework.",
        quality_checklist=_base_quality_checklist()
        + ["The chapter has characters.", "The chapter has conflict.", "The chapter has a consequence and lesson."],
    )
