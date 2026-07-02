from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.rss_feed_connector import FeedRegistry, feed_rows
from app.source_recommender import recommend_sources
from app.storage import SignalStore


@dataclass(frozen=True)
class FeedCandidate:
    name: str
    url: str
    category: str
    why: str
    intake_note: str


@dataclass(frozen=True)
class IntakeCommand:
    title: str
    command: str
    purpose: str


def configured_source_rows(settings: Settings) -> list[dict[str, object]]:
    return [
        {
            "enabled": source.enabled,
            "name": source.name,
            "handle": source.handle,
            "trust_score": source.trust_score,
            "category_hint": source.category_hint,
            "min_save_score": source.min_save_score if source.min_save_score is not None else "default",
            "destination": source.destination,
            "notes": source.notes,
        }
        for source in settings.source_registry.sources
    ]


def configured_feed_rows(feeds_path: str = "feeds.yaml") -> list[dict[str, object]]:
    registry = FeedRegistry.from_yaml(Path(feeds_path))
    return feed_rows(registry)


def source_quality_rows(store: SignalStore) -> list[dict[str, object]]:
    return store.source_stats()


def source_recommendation_rows(store: SignalStore, min_samples: int = 10) -> list[dict[str, object]]:
    return [
        {
            "source": item.source_title,
            "action": item.action,
            "total": item.total,
            "useful": item.valuable,
            "sent": item.sent,
            "signal_ratio": round(item.signal_ratio, 1),
            "avg_score": round(item.avg_score, 1),
            "max_score": round(item.max_score, 1),
            "suggested_min_save_score": item.suggested_min_save_score or "-",
            "reason": item.reason,
        }
        for item in recommend_sources(store.source_stats(), min_samples=min_samples)
    ]


def intake_commands(limit: int = 20, send: bool = False) -> list[IntakeCommand]:
    send_flag = " --send" if send else ""
    return [
        IntakeCommand(
            title="Telegram backfill now",
            command=f"python -m app.main backfill --limit {limit}{send_flag}",
            purpose="Fetch recent historical Telegram messages from configured sources and analyze them.",
        ),
        IntakeCommand(
            title="RSS/blog backfill now",
            command=f"python -m app.rss_cli backfill --feeds feeds.yaml --limit {limit}{send_flag}",
            purpose="Fetch recent RSS/blog feed entries and process them through the same signal analyzer with feed-specific thresholds and routing.",
        ),
        IntakeCommand(
            title="RSS/blog full article backfill",
            command=f"python -m app.rss_cli backfill --feeds feeds.yaml --limit {limit} --fetch-articles{send_flag}",
            purpose="Fetch feed entries, extract full article text with Trafilatura, and analyze richer signals with feed-specific thresholds and routing.",
        ),
        IntakeCommand(
            title="Show RSS/blog feeds",
            command="python -m app.rss_cli feeds --feeds feeds.yaml",
            purpose="Print configured RSS/blog feed metadata from feeds.yaml.",
        ),
        IntakeCommand(
            title="Run due schedules once",
            command="python -m app.intake_scheduler_cli run-due",
            purpose="Run due intake scheduler jobs once and mark successful jobs as run.",
        ),
        IntakeCommand(
            title="List due schedules",
            command="python -m app.intake_scheduler_cli due",
            purpose="Show due intake scheduler jobs without running them.",
        ),
        IntakeCommand(
            title="Live Telegram monitor",
            command="python -m app.main monitor",
            purpose="Keep listening for new Telegram messages until you stop the process.",
        ),
        IntakeCommand(
            title="Show Telegram sources",
            command="python -m app.main sources",
            purpose="Print configured Telegram source metadata from sources.yaml.",
        ),
        IntakeCommand(
            title="Source quality stats",
            command="python -m app.main stats",
            purpose="Show which sources are producing useful signals.",
        ),
        IntakeCommand(
            title="Tune source thresholds",
            command="python -m app.main recommend-sources --min-samples 10",
            purpose="Recommend which sources to keep, raise threshold for, or disable.",
        ),
    ]


def command_rows(commands: list[IntakeCommand]) -> list[dict[str, str]]:
    return [{"title": item.title, "command": item.command, "purpose": item.purpose} for item in commands]


def scheduler_snippets(limit: int = 20) -> dict[str, str]:
    return {
        "scheduler_runner_every_hour": "0 * * * * cd /path/to/tele-scraper-brain && . .venv/bin/activate && python -m app.intake_scheduler_cli run-due >> logs/intake-scheduler.log 2>&1",
        "scheduler_runner_dry_run": "cd /path/to/tele-scraper-brain && . .venv/bin/activate && python -m app.intake_scheduler_cli run-due --dry-run",
        "list_due_schedules": "cd /path/to/tele-scraper-brain && . .venv/bin/activate && python -m app.intake_scheduler_cli due",
        "telegram_cron_every_2_hours": f"0 */2 * * * cd /path/to/tele-scraper-brain && . .venv/bin/activate && python -m app.main backfill --limit {limit} >> logs/telegram-backfill.log 2>&1",
        "rss_cron_every_4_hours": f"0 */4 * * * cd /path/to/tele-scraper-brain && . .venv/bin/activate && python -m app.rss_cli backfill --feeds feeds.yaml --limit {limit} >> logs/rss-backfill.log 2>&1",
        "manual_telegram_monitor": "cd /path/to/tele-scraper-brain && . .venv/bin/activate && python -m app.main monitor",
    }


def recommended_feed_candidates() -> list[FeedCandidate]:
    return [
        FeedCandidate("OpenAI Blog", "https://openai.com/blog/rss.xml", "AI Engineering", "Model, product, and platform updates that influence real AI engineering decisions.", "Add to feeds.yaml for RSS intake."),
        FeedCandidate("Anthropic Engineering", "https://www.anthropic.com/engineering", "AI Engineering", "Strong engineering posts on agents, evals, context, safety, and production AI workflows.", "Track manually if no RSS feed is available."),
        FeedCandidate("GitHub Blog - AI & ML", "https://github.blog/ai-and-ml/feed/", "Tools", "Useful for Copilot, developer workflow, code agents, and software engineering productivity.", "Add to feeds.yaml for RSS intake."),
        FeedCandidate("AWS Machine Learning Blog", "https://aws.amazon.com/blogs/machine-learning/feed/", "AI Engineering", "Good source for Bedrock, AWS architecture, MLOps, and production AI system patterns.", "Add to feeds.yaml for RSS intake."),
        FeedCandidate("Google DeepMind Blog", "https://deepmind.google/discover/blog/", "Research", "Useful for foundation-model, agents, robotics, and research-level developments.", "Track as research source; summarize only high-signal posts."),
        FeedCandidate("Microsoft Research Blog", "https://www.microsoft.com/en-us/research/blog/", "Research", "Good for applied research, systems, AI agents, and academic-to-product insights.", "Use as a research watch source."),
        FeedCandidate("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "Tools", "Practical open-source models, datasets, agents, and developer tools.", "Add to feeds.yaml for RSS intake."),
        FeedCandidate("Latent Space", "https://www.latent.space/feed", "Content", "Strong AI engineering and market context useful for article ideas and technical storytelling.", "Use for creator inspiration; do not ingest every post blindly."),
        FeedCandidate("The Batch by DeepLearning.AI", "https://www.deeplearning.ai/the-batch/", "AI Engineering", "Compact AI news with strong learning value for weekly briefings.", "Good candidate for digest-style intake."),
        FeedCandidate("Lenny's Newsletter", "https://www.lennysnewsletter.com/feed", "Product", "Useful for product thinking, growth, strategy, and turning AI signals into product narratives.", "Use selectively for product-angle content."),
    ]


def feed_candidate_rows() -> list[dict[str, str]]:
    return [
        {
            "name": item.name,
            "url": item.url,
            "category": item.category,
            "why": item.why,
            "intake_note": item.intake_note,
        }
        for item in recommended_feed_candidates()
    ]
