from __future__ import annotations

from dataclasses import dataclass

from app.idea_lab import IdeaLabReport


ALLOWED_SERIES_TYPES = {
    "linkedin_series",
    "medium_series",
    "course_series",
    "podcast_series",
    "storybook_series",
}


@dataclass(frozen=True)
class SeriesEpisode:
    index: int
    title: str
    purpose: str
    format: str
    outline: list[str]
    call_to_action: str

    def render(self) -> str:
        lines = [
            f"### Episode {self.index}: {self.title}",
            "",
            f"Format: {self.format}",
            f"Purpose: {self.purpose}",
            "",
            "Outline:",
        ]
        lines.extend(f"- {item}" for item in self.outline)
        lines.extend(["", f"Call to action: {self.call_to_action}"])
        return "\n".join(lines).strip()


@dataclass(frozen=True)
class ContentSeries:
    signal_id: int
    source: str
    series_type: str
    title: str
    audience: str
    promise: str
    narrative_arc: str
    episodes: list[SeriesEpisode]
    reuse_plan: list[str]
    quality_checklist: list[str]

    def render(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"Series type: {self.series_type}",
            f"Signal ID: {self.signal_id}",
            f"Source: {self.source}",
            "",
            "## Audience",
            self.audience,
            "",
            "## Promise",
            self.promise,
            "",
            "## Narrative Arc",
            self.narrative_arc,
            "",
            "## Episodes",
        ]
        lines.extend(episode.render() for episode in self.episodes)
        lines.extend(["", "## Reuse Plan"])
        lines.extend(f"- {item}" for item in self.reuse_plan)
        lines.extend(["", "## Quality Checklist"])
        lines.extend(f"- [ ] {item}" for item in self.quality_checklist)
        return "\n".join(lines).strip()


def normalize_series_type(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_SERIES_TYPES:
        allowed = ", ".join(sorted(ALLOWED_SERIES_TYPES))
        raise ValueError(f"Unsupported series type '{value}'. Allowed series types: {allowed}")
    return normalized


def generate_series(report: IdeaLabReport, series_type: str, episode_count: int = 5) -> ContentSeries:
    normalized_type = normalize_series_type(series_type)
    count = normalize_episode_count(episode_count)
    builders = {
        "linkedin_series": _linkedin_series,
        "medium_series": _medium_series,
        "course_series": _course_series,
        "podcast_series": _podcast_series,
        "storybook_series": _storybook_series,
    }
    return builders[normalized_type](report, count)


def normalize_episode_count(value: int) -> int:
    count = int(value)
    if count < 3 or count > 10:
        raise ValueError("episode_count must be between 3 and 10.")
    return count


def _topic(report: IdeaLabReport) -> str:
    if report.title_ideas:
        return report.title_ideas[0]
    return report.category


def _base_quality_checklist() -> list[str]:
    return [
        "Each episode has a distinct purpose.",
        "The series has a clear beginning, middle, and end.",
        "The reader journey moves from awareness to application.",
        "At least one episode includes a practical framework or example.",
        "The series can be repurposed into another format.",
    ]


def _reuse_plan(series_type: str) -> list[str]:
    return [
        "Turn the strongest episode into a standalone LinkedIn post.",
        "Combine all episodes into a long-form article outline.",
        "Reuse the framework as a teaching exercise.",
        "Convert the narrative arc into a podcast or story chapter later.",
        f"Track the series in Publishing Queue as {series_type}.",
    ]


def _episode_titles(prefixes: list[str], count: int) -> list[str]:
    while len(prefixes) < count:
        prefixes.append(f"Part {len(prefixes) + 1}: Apply the framework")
    return prefixes[:count]


def _make_episodes(titles: list[str], report: IdeaLabReport, content_format: str) -> list[SeriesEpisode]:
    episodes: list[SeriesEpisode] = []
    for index, title in enumerate(titles, start=1):
        episodes.append(
            SeriesEpisode(
                index=index,
                title=title,
                purpose=_episode_purpose(index, report),
                format=content_format,
                outline=_episode_outline(index, report),
                call_to_action=_episode_cta(index),
            )
        )
    return episodes


def _episode_purpose(index: int, report: IdeaLabReport) -> str:
    purposes = [
        "Introduce the signal and why it matters.",
        "Reveal the hidden gap most readers miss.",
        "Convert the insight into a practical framework.",
        "Show a realistic example, trade-off, or failure mode.",
        "Close with a reusable action plan for the reader.",
    ]
    if index <= len(purposes):
        return purposes[index - 1]
    return f"Extend the series with a deeper application of {report.category}."


def _episode_outline(index: int, report: IdeaLabReport) -> list[str]:
    outlines = {
        1: [report.core_insight, "Explain the source context.", "State the reader problem."],
        2: [report.hidden_gap, "Show the common shallow interpretation.", "Explain what better thinkers notice."],
        3: [report.novel_angle, "Name the framework.", "Break the framework into steps."],
        4: ["Create a real-world scenario.", "Show one trade-off.", "Show one failure mode."],
        5: ["Summarize the full arc.", "Give a checklist.", "Ask the reader to apply it to one signal."],
    }
    return outlines.get(index, ["Add one deeper example.", "Connect it to the series promise.", "Give a practical next step."])


def _episode_cta(index: int) -> str:
    if index == 1:
        return "Save one signal worth thinking about, not just reading."
    if index == 2:
        return "Write the hidden gap behind one saved link."
    if index == 3:
        return "Turn the idea into a simple framework."
    if index == 4:
        return "Add one example and one trade-off."
    return "Turn the series into a queue item and schedule the next draft."


def _linkedin_series(report: IdeaLabReport, count: int) -> ContentSeries:
    titles = _episode_titles(
        [
            "The signal most builders would only save",
            "The hidden gap behind the signal",
            "The Signal-to-Blueprint method",
            "A practical example for builders",
            "Your weekly signal extraction habit",
        ],
        count,
    )
    return ContentSeries(
        signal_id=report.signal_id,
        source=report.source,
        series_type="linkedin_series",
        title=f"LinkedIn Series: {_topic(report)}",
        audience="Builders, AI engineers, and technical creators scrolling for practical insight.",
        promise="Help readers turn one technical signal into original thinking and action.",
        narrative_arc="Awareness -> hidden gap -> framework -> example -> habit.",
        episodes=_make_episodes(titles, report, "LinkedIn post"),
        reuse_plan=_reuse_plan("linkedin_series"),
        quality_checklist=_base_quality_checklist() + ["Each post can stand alone in the feed."],
    )


def _medium_series(report: IdeaLabReport, count: int) -> ContentSeries:
    titles = _episode_titles(
        [
            "Why one signal deserves a full article",
            "The engineering gap beneath the headline",
            "A practical framework for applying the signal",
            "Trade-offs, examples, and failure modes",
            "How to build a repeatable signal-to-content system",
        ],
        count,
    )
    return ContentSeries(
        signal_id=report.signal_id,
        source=report.source,
        series_type="medium_series",
        title=f"Medium Series: {_topic(report)}",
        audience="Technical readers who want depth, structure, and reusable frameworks.",
        promise="Create a multi-article path from context to practical implementation.",
        narrative_arc="Context -> analysis -> framework -> implementation -> operating model.",
        episodes=_make_episodes(titles, report, "Medium article"),
        reuse_plan=_reuse_plan("medium_series"),
        quality_checklist=_base_quality_checklist() + ["Each article adds new depth rather than repeating the same point."],
    )


def _course_series(report: IdeaLabReport, count: int) -> ContentSeries:
    titles = _episode_titles(
        [
            "Learning from a real signal",
            "Separating useful insight from noise",
            "Building the practical framework",
            "Hands-on mini task",
            "Assessment and reflection",
        ],
        count,
    )
    return ContentSeries(
        signal_id=report.signal_id,
        source=report.source,
        series_type="course_series",
        title=f"Course Series: {report.category} From Signals to Practice",
        audience="Students, junior engineers, and workshop participants.",
        promise="Turn one real signal into a teachable sequence with practice and assessment.",
        narrative_arc="Observe -> classify -> build -> practice -> reflect.",
        episodes=_make_episodes(titles, report, "Course lesson"),
        reuse_plan=_reuse_plan("course_series"),
        quality_checklist=_base_quality_checklist() + ["Each lesson has a learner task."],
    )


def _podcast_series(report: IdeaLabReport, count: int) -> ContentSeries:
    titles = _episode_titles(
        [
            "The saved signal that started the conversation",
            "What the obvious take misses",
            "The framework behind the signal",
            "A team story and trade-off",
            "The listener's weekly practice",
        ],
        count,
    )
    return ContentSeries(
        signal_id=report.signal_id,
        source=report.source,
        series_type="podcast_series",
        title=f"Podcast Series: {_topic(report)}",
        audience="Technical listeners who prefer story-led practical explanation.",
        promise="Make the signal memorable through conversation, conflict, and takeaway.",
        narrative_arc="Scene -> tension -> explanation -> trade-off -> takeaway.",
        episodes=_make_episodes(titles, report, "Podcast episode"),
        reuse_plan=_reuse_plan("podcast_series"),
        quality_checklist=_base_quality_checklist() + ["Each episode is speakable aloud."],
    )


def _storybook_series(report: IdeaLabReport, count: int) -> ContentSeries:
    titles = _episode_titles(
        [
            "The team finds the signal",
            "The team misunderstands the gap",
            "The framework emerges under pressure",
            "The failure mode becomes visible",
            "The team changes how it works",
        ],
        count,
    )
    return ContentSeries(
        signal_id=report.signal_id,
        source=report.source,
        series_type="storybook_series",
        title=f"Storybook Series: The Team That Learned {report.category} the Hard Way",
        audience="Readers who enjoy technical ideas through realistic workplace stories.",
        promise="Teach the technical idea through character, conflict, consequence, and transformation.",
        narrative_arc="Character -> context -> conflict -> decision -> consequence -> lesson.",
        episodes=_make_episodes(titles, report, "Story chapter"),
        reuse_plan=_reuse_plan("storybook_series"),
        quality_checklist=_base_quality_checklist() + ["Each chapter has conflict and transformation."],
    )
