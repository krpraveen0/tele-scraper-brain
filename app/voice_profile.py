from __future__ import annotations

from dataclasses import dataclass
import re


ALLOWED_VOICE_SURFACES = {
    "linkedin",
    "medium",
    "course",
    "podcast",
    "storybook",
    "general",
}

VOICE_SURFACE_ALIASES = {
    "story_book": "storybook",
    "story_books": "storybook",
    "story_book_chapter": "storybook",
    "story_chapter": "storybook",
}

GENERIC_AI_PHRASES = (
    "in today's fast-paced world",
    "unlock the power",
    "game-changer",
    "revolutionize",
    "delve into",
    "seamlessly",
    "cutting-edge",
    "leverage the power",
    "transform your workflow",
)


@dataclass(frozen=True)
class VoiceProfile:
    name: str
    positioning: str
    tone_rules: list[str]
    structure_rules: list[str]
    preferred_phrases: list[str]
    banned_phrases: list[str]
    surface_guidance: dict[str, list[str]]

    def guidance_for(self, surface: str = "general") -> list[str]:
        normalized = normalize_surface(surface)
        return self.surface_guidance.get(normalized, self.surface_guidance["general"])

    def render(self, surface: str = "general") -> str:
        lines = [
            f"# {self.name}",
            "",
            "## Positioning",
            self.positioning,
            "",
            "## Tone Rules",
        ]
        lines.extend(f"- {rule}" for rule in self.tone_rules)
        lines.extend(["", "## Structure Rules"])
        lines.extend(f"- {rule}" for rule in self.structure_rules)
        lines.extend(["", "## Preferred Phrases"])
        lines.extend(f"- {phrase}" for phrase in self.preferred_phrases)
        lines.extend(["", "## Banned Phrases"])
        lines.extend(f"- {phrase}" for phrase in self.banned_phrases)
        lines.extend(["", f"## Surface Guidance: {normalize_surface(surface)}"])
        lines.extend(f"- {rule}" for rule in self.guidance_for(surface))
        return "\n".join(lines).strip()


@dataclass(frozen=True)
class VoiceReview:
    surface: str
    score: float
    strengths: list[str]
    issues: list[str]
    suggestions: list[str]

    def render(self) -> str:
        lines = [
            "# Voice Review",
            "",
            f"Surface: {self.surface}",
            f"Score: {self.score:.1f}/10",
            "",
            "## Strengths",
        ]
        lines.extend(f"- {item}" for item in self.strengths)
        lines.extend(["", "## Issues"])
        lines.extend(f"- {item}" for item in self.issues)
        lines.extend(["", "## Suggestions"])
        lines.extend(f"- {item}" for item in self.suggestions)
        return "\n".join(lines).strip()


def normalize_surface(value: str) -> str:
    normalized = str(value or "general").strip().lower().replace("-", "_").replace(" ", "_")
    normalized = VOICE_SURFACE_ALIASES.get(normalized, normalized)
    if normalized not in ALLOWED_VOICE_SURFACES:
        allowed = ", ".join(sorted(ALLOWED_VOICE_SURFACES))
        raise ValueError(f"Unsupported voice surface '{value}'. Allowed surfaces: {allowed}")
    return normalized


def default_praveen_voice_profile() -> VoiceProfile:
    return VoiceProfile(
        name="Praveen Voice Profile",
        positioning="Practical AI engineer, builder, trainer, and technical storyteller who explains systems through real workflows, trade-offs, and human learning moments.",
        tone_rules=[
            "Sound like a working engineer, not a marketing page.",
            "Prefer direct, human, slightly conversational language.",
            "Show the practical pain before naming the framework.",
            "Include trade-offs, failure modes, or debugging lessons when possible.",
            "Respect the reader's intelligence; avoid over-explaining obvious points.",
        ],
        structure_rules=[
            "Open with a concrete situation, mistake, or decision point.",
            "Move from signal to insight, then to framework and action.",
            "Use short paragraphs and clear section headers.",
            "Make the reader feel this came from actual building or teaching experience.",
            "End with one practical action, not a generic inspirational sentence.",
        ],
        preferred_phrases=[
            "Here is the practical part",
            "The mistake I see is",
            "What changed my thinking was",
            "In a real workflow",
            "The trade-off is",
            "This becomes useful only when",
        ],
        banned_phrases=list(GENERIC_AI_PHRASES),
        surface_guidance={
            "linkedin": [
                "Start with a sharp observation or personal workflow pain.",
                "Keep paragraphs short and skimmable.",
                "Avoid sounding like a polished AI announcement.",
            ],
            "medium": [
                "Add depth, examples, diagrams, and trade-offs.",
                "Use a clear narrative arc from problem to framework.",
                "Make the article useful even without prior context.",
            ],
            "course": [
                "Use trainer-friendly steps, learner tasks, and checks for understanding.",
                "Explain jargon in plain English before adding complexity.",
                "Include mistakes students are likely to make.",
            ],
            "podcast": [
                "Make the writing speakable aloud.",
                "Use story tension and conversational transitions.",
                "Repeat the main lesson in one memorable sentence.",
            ],
            "storybook": [
                "Teach through character, conflict, and consequence.",
                "Keep the technical lesson visible without turning the story into notes.",
                "Show how the character changes behavior.",
            ],
            "general": [
                "Be practical, honest, and builder-led.",
                "Prefer concrete examples over abstract claims.",
                "Remove generic AI hype before publishing.",
            ],
        },
    )


def review_voice(text: str, surface: str = "general", profile: VoiceProfile | None = None) -> VoiceReview:
    normalized_surface = normalize_surface(surface)
    active_profile = profile or default_praveen_voice_profile()
    clean_text = text.strip()
    lowered = clean_text.lower()

    issues: list[str] = []
    strengths: list[str] = []
    suggestions: list[str] = []
    score = 10.0

    banned_hits = [phrase for phrase in active_profile.banned_phrases if phrase in lowered]
    if banned_hits:
        score -= min(3.0, len(banned_hits) * 0.8)
        issues.append(f"Generic AI phrases detected: {', '.join(banned_hits)}")
        suggestions.append("Replace hype phrases with a concrete workflow, mistake, or trade-off.")
    else:
        strengths.append("Avoids obvious AI-hype phrases.")

    if _has_practical_marker(lowered):
        strengths.append("Includes practical builder/trainer language.")
    else:
        score -= 1.5
        issues.append("Needs a more practical builder-led anchor.")
        suggestions.append("Add a phrase like 'in a real workflow', 'the trade-off is', or 'the mistake I see is'.")

    if _has_tradeoff_marker(lowered):
        strengths.append("Mentions trade-offs, mistakes, or failure modes.")
    else:
        score -= 1.0
        issues.append("No trade-off, mistake, or failure mode is visible.")
        suggestions.append("Add one concrete failure mode or decision trade-off.")

    avg_sentence_length = _average_sentence_length(clean_text)
    if avg_sentence_length > 28:
        score -= 1.0
        issues.append("Sentences are long for Praveen's preferred direct style.")
        suggestions.append("Break long sentences into shorter practical statements.")
    else:
        strengths.append("Sentence length is reasonably readable.")

    if normalized_surface == "linkedin" and len(clean_text.split()) > 280:
        score -= 1.0
        issues.append("LinkedIn draft may be too long for quick reading.")
        suggestions.append("Trim to one sharp idea, one example, and one action.")

    if not clean_text:
        score = 0.0
        issues = ["Text is empty."]
        suggestions = ["Add a draft before reviewing voice."]
        strengths = []

    return VoiceReview(
        surface=normalized_surface,
        score=max(0.0, min(10.0, score)),
        strengths=strengths,
        issues=issues,
        suggestions=suggestions or active_profile.guidance_for(normalized_surface),
    )


def build_voice_prompt(surface: str = "general", profile: VoiceProfile | None = None) -> str:
    active_profile = profile or default_praveen_voice_profile()
    normalized_surface = normalize_surface(surface)
    lines = [
        "Write in Praveen's voice.",
        "",
        f"Positioning: {active_profile.positioning}",
        "",
        "Tone rules:",
    ]
    lines.extend(f"- {rule}" for rule in active_profile.tone_rules)
    lines.extend(["", "Structure rules:"])
    lines.extend(f"- {rule}" for rule in active_profile.structure_rules)
    lines.extend(["", f"Surface guidance for {normalized_surface}:"])
    lines.extend(f"- {rule}" for rule in active_profile.guidance_for(normalized_surface))
    lines.extend(["", "Avoid:"])
    lines.extend(f"- {phrase}" for phrase in active_profile.banned_phrases)
    return "\n".join(lines).strip()


def _has_practical_marker(text: str) -> bool:
    markers = ("workflow", "practical", "building", "debug", "teaching", "example", "real", "trainer")
    return any(marker in text for marker in markers)


def _has_tradeoff_marker(text: str) -> bool:
    markers = ("trade-off", "tradeoff", "mistake", "failure", "risk", "cost", "constraint", "debug")
    return any(marker in text for marker in markers)


def _average_sentence_length(text: str) -> float:
    sentences = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    if not sentences:
        return 0.0
    return sum(len(sentence.split()) for sentence in sentences) / len(sentences)
