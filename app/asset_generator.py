from __future__ import annotations

from dataclasses import dataclass
from textwrap import shorten

from app.models import StoredSignal


ALLOWED_ASSET_TYPES = {
    "linkedin",
    "medium_outline",
    "teaching_example",
    "career_note",
    "english_practice",
    "research_note",
    "tool_review",
}


@dataclass(frozen=True)
class GeneratedAsset:
    signal_id: int
    asset_type: str
    title: str
    body: str

    def render(self) -> str:
        return f"# {self.title}\n\n{self.body}".strip()


def generate_asset(signal: StoredSignal, asset_type: str) -> GeneratedAsset:
    normalized_type = asset_type.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized_type not in ALLOWED_ASSET_TYPES:
        allowed = ", ".join(sorted(ALLOWED_ASSET_TYPES))
        raise ValueError(f"Unsupported asset type '{asset_type}'. Allowed asset types: {allowed}")

    builders = {
        "linkedin": _linkedin_asset,
        "medium_outline": _medium_outline_asset,
        "teaching_example": _teaching_example_asset,
        "career_note": _career_note_asset,
        "english_practice": _english_practice_asset,
        "research_note": _research_note_asset,
        "tool_review": _tool_review_asset,
    }
    return builders[normalized_type](signal)


def _summary(signal: StoredSignal) -> str:
    return signal.analysis.summary or signal.analysis.reason or shorten(signal.message_text, width=220, placeholder="...")


def _tags(signal: StoredSignal) -> str:
    return " ".join(signal.analysis.tags) if signal.analysis.tags else "#signalos"


def _source_line(signal: StoredSignal) -> str:
    permalink = f"\nSource link: {signal.permalink}" if signal.permalink else ""
    return f"Source: {signal.source_title}{permalink}"


def _linkedin_asset(signal: StoredSignal) -> GeneratedAsset:
    body = f"""Most useful signals rarely look useful at first glance.

Today's signal from {signal.source_title} points to this idea:

{_summary(signal)}

My takeaway:
A personal AI system should not just collect information. It should filter, score, route, and learn from feedback.

Why this matters:
- Career growth needs targeted signals, not endless scrolling
- AI engineering needs patterns worth testing
- Teaching needs real examples
- Content needs fresh but practical ideas

This is why I am building Signal OS as a feedback-driven system, not just a scraper.

{_tags(signal)}"""
    return GeneratedAsset(signal_id=signal.id, asset_type="linkedin", title="LinkedIn Draft", body=body.strip())


def _medium_outline_asset(signal: StoredSignal) -> GeneratedAsset:
    body = f"""Working title:
{_summary(signal)}

Target reader:
Software engineers, AI engineers, builders, and technical trainers.

Opening hook:
Most engineers do not need more information sources. They need a better way to turn noisy sources into useful judgment.

Outline:
1. The problem: too much information, too little signal
2. Why this signal is worth paying attention to
3. What it reveals about career, AI engineering, or teaching
4. A practical architecture or workflow inspired by it
5. How to test the idea locally
6. Mistakes and risks to avoid
7. Final takeaway for builders

Source notes:
{_source_line(signal)}

Useful tags:
{_tags(signal)}"""
    return GeneratedAsset(signal_id=signal.id, asset_type="medium_outline", title="Medium Outline", body=body.strip())


def _teaching_example_asset(signal: StoredSignal) -> GeneratedAsset:
    body = f"""Teaching topic:
Use a real-world signal as a classroom example.

Source signal:
{_summary(signal)}

How to teach it:
1. Show students the raw message.
2. Ask them what is useful and what is noise.
3. Convert the message into structured fields: category, score, action, tags.
4. Discuss why automation needs human feedback.
5. Turn the example into a small Python exercise.

Possible Python exercise:
Create a list of saved signals and use dictionaries or collections.Counter to count categories, tags, and high-score items.

Discussion question:
What makes this signal useful for a learner, engineer, or content creator?

{_source_line(signal)}"""
    return GeneratedAsset(signal_id=signal.id, asset_type="teaching_example", title="Teaching Example", body=body.strip())


def _career_note_asset(signal: StoredSignal) -> GeneratedAsset:
    body = f"""Career signal:
{_summary(signal)}

Why it may matter:
This signal connects to your career growth if it mentions AI engineering, product companies, remote work, RAG, agents, Python, cloud, or production LLM systems.

What to extract:
- Skills mentioned
- Company or role context
- Tools/frameworks
- Seniority expectations
- Portfolio or resume keywords

Action plan:
1. Save the key skills.
2. Check if your resume shows proof for those skills.
3. Convert one missing skill into a weekend project.
4. Add one interview preparation note.

Suggested resume keywords:
agentic AI, RAG, Python backend, LLM evaluation, observability, production AI systems

{_source_line(signal)}"""
    return GeneratedAsset(signal_id=signal.id, asset_type="career_note", title="Career Note", body=body.strip())


def _english_practice_asset(signal: StoredSignal) -> GeneratedAsset:
    body = f"""Speaking practice theme:
Explain this signal clearly in a work meeting.

Signal:
{_summary(signal)}

Simple version:
I found one useful signal today. It is about {signal.analysis.category.lower()}. The main point is that it may help us decide what to learn, build, or ignore.

Leadership version:
Before we act on this, let us separate the actual signal from the noise. The useful part is the practical implication, not just the headline.

Practice task:
Say this in 30 seconds:
- What did I find?
- Why is it useful?
- What should we do next?

Useful phrases:
- "The key takeaway is..."
- "This is relevant because..."
- "My recommendation is..."
- "Let us validate this before investing more time."

{_source_line(signal)}"""
    return GeneratedAsset(signal_id=signal.id, asset_type="english_practice", title="English Practice", body=body.strip())


def _research_note_asset(signal: StoredSignal) -> GeneratedAsset:
    body = f"""Research note:
{_summary(signal)}

Why it is worth tracking:
This signal may connect to agentic AI, RAG, memory, evaluation, context engineering, local LLMs, or production AI systems.

Questions to investigate:
1. What problem does this solve?
2. Is there a paper, repo, benchmark, or case study behind it?
3. Can it improve your multi-agent or Signal OS work?
4. What experiment could validate it locally?

Mini research task:
Find one primary source, one implementation example, and one limitation.

{_source_line(signal)}

Tags:
{_tags(signal)}"""
    return GeneratedAsset(signal_id=signal.id, asset_type="research_note", title="Research Note", body=body.strip())


def _tool_review_asset(signal: StoredSignal) -> GeneratedAsset:
    body = f"""Tool/repo review note:
{_summary(signal)}

Evaluation checklist:
- What problem does it solve?
- Does it fit your AI engineering or teaching workflow?
- Is it active and maintained?
- Can it run locally or mostly free?
- Can it become a demo, workshop, or portfolio project?

Try-it plan:
1. Read the README or docs.
2. Run the smallest local example.
3. Note setup friction.
4. Decide: ignore, archive, use in class, or build with it.

Output to create if useful:
- LinkedIn mini-review
- Teaching demo
- Medium article section
- Architecture diagram

{_source_line(signal)}"""
    return GeneratedAsset(signal_id=signal.id, asset_type="tool_review", title="Tool Review", body=body.strip())
