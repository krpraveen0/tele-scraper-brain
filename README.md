# Praveen Signal OS

A local-first personal intelligence system that monitors Telegram sources, filters noisy posts, scores useful signals with a local LLM/backend, stores them in SQLite, and sends high-value summaries back to your private Telegram channels.

This MVP focuses on Telegram + SQLite with either Ollama or OpenCode as the analysis backend.

## What it does

- Monitors selected Telegram channels/groups using Telethon.
- Can backfill recent historical messages for immediate testing.
- Cleans and deduplicates messages.
- Applies a cheap rule-based pre-filter before using the LLM/backend.
- Uses Ollama or OpenCode to classify, summarize, score, and recommend an action.
- Supports source-aware thresholds through `sources.yaml`.
- Routes saved signals by source destination or analysis category.
- Stores every evaluated signal in SQLite.
- Supports feedback labels so your judgment can be captured over time.
- Generates reusable asset drafts from saved signals.
- Can show sent saved signals, unsent saved signals, source config, source stats, source recommendations, feedback summaries, asset drafts, and daily briefings.

## Core streams

The system is designed around your personal goals:

- Career radar for remote AI/full-stack roles.
- AI engineering radar for agentic AI, RAG, local LLMs, observability, and production AI systems.
- Teaching vault for Python, GenAI, FastAPI, Colab/Kaggle, and project-driven training ideas.
- Content engine for LinkedIn and Medium ideas.
- Spoken English practice for leadership communication.
- Research and tool radar.

## Project structure

```text
tele-scraper-brain/
├── app/
│   ├── __init__.py
│   ├── asset_generator.py
│   ├── config.py
│   ├── daily_briefing.py
│   ├── dedupe.py
│   ├── llm_filter.py
│   ├── llm_provider.py
│   ├── main.py
│   ├── message_cleaner.py
│   ├── models.py
│   ├── rule_filter.py
│   ├── signal_processor.py
│   ├── source_recommender.py
│   ├── sources.py
│   ├── storage.py
│   └── telegram_client.py
├── data/
│   └── .gitkeep
├── prompts/
│   └── classify_message.txt
├── tests/
├── sources.curated.yaml
├── sources.example.yaml
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Requirements

- Python 3.10+
- Telegram API credentials from https://my.telegram.org
- Either Ollama or OpenCode installed locally
- A private Telegram channel/group where the bot/user client can post saved signals

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with your values.

## Source intelligence

Use `sources.yaml` to control source quality, category hints, thresholds, and routing.

For a minimal template:

```bash
cp sources.example.yaml sources.yaml
```

For a web-validated curated starter pack:

```bash
cp sources.curated.yaml sources.yaml
```

The curated pack intentionally contains only exact public handles that resolved during validation. It does not include placeholder/dummy channels. It is still only a starting point: Telegram has clones, stale channels, and scam channels, so validate quality with the local `stats` command before keeping a source enabled.

Example source entry:

```yaml
sources:
  - name: Moneycontrol
    handle: "@moneycontrolcom"
    enabled: true
    trust_score: 8
    category_hint: Global Economy
    min_save_score: 8.3
    destination: global_economy
```

When `sources.yaml` exists, it becomes the preferred source list. If it does not exist, the app falls back to legacy `SOURCE_CHATS` from `.env`.

Inspect configured sources:

```bash
python -m app.main sources
```

Inspect source quality from stored data:

```bash
python -m app.main stats
```

Generate deterministic tuning recommendations from local SQLite stats:

```bash
python -m app.main recommend-sources
```

Use a larger sample threshold when you want more conservative advice:

```bash
python -m app.main recommend-sources --min-samples 25
```

Recommended validation loop:

```bash
python -m app.main backfill --limit 20
python -m app.main stats
python -m app.main recommend-sources
```

The recommendation command does not edit `sources.yaml`. It tells you what to change manually, such as disabling a source, raising `min_save_score`, or keeping a high-value source.

## Feedback labels

Use feedback labels to capture your judgment after reviewing saved signals. This is the first step toward making the system Praveen-aware instead of only score-aware.

First list saved signal IDs:

```bash
python -m app.main unsent --limit 20
python -m app.main recent --limit 20
```

Then label useful or noisy signals:

```bash
python -m app.main feedback --id 123 --label useful
python -m app.main feedback --id 124 --label not_useful --notes "Too generic"
python -m app.main feedback --id 125 --label linkedin_idea
python -m app.main feedback --id 126 --label teaching_example
python -m app.main feedback --id 127 --label career_opportunity
python -m app.main feedback --id 128 --label read_weekend
```

Allowed labels:

```text
archive, career_opportunity, economy_signal, english_practice, linkedin_idea, medium_idea, not_useful, read_today, read_weekend, research_note, teaching_example, tool_to_try, useful
```

Inspect feedback history:

```bash
python -m app.main feedback-summary
python -m app.main feedback-recent --limit 20
```

The feedback commands do not change LLM prompts yet. They create a clean judgment dataset that later phases can use for prompt tuning, asset generation, and Telegram buttons.

## Asset generation

Use asset generation to turn one saved signal into a reusable draft for your real goals: LinkedIn, Medium, teaching, career prep, English practice, research, or tool review.

First list signal IDs:

```bash
python -m app.main unsent --limit 20
python -m app.main recent --limit 20
```

Then create an asset:

```bash
python -m app.main create-asset --id 123 --type linkedin
python -m app.main create-asset --id 123 --type medium_outline
python -m app.main create-asset --id 123 --type teaching_example
python -m app.main create-asset --id 123 --type career_note
python -m app.main create-asset --id 123 --type english_practice
python -m app.main create-asset --id 123 --type research_note
python -m app.main create-asset --id 123 --type tool_review
```

Supported asset types:

```text
career_note, english_practice, linkedin, medium_outline, research_note, teaching_example, tool_review
```

Phase 7 asset generation is deterministic and print-only. It does not call the LLM and does not save generated assets yet. This keeps the first version fast, testable, and safe. Later phases can add LLM rewriting, Markdown export, SQLite asset history, and sending generated assets to Telegram.

Recommended signal-to-asset workflow:

```bash
python -m app.main unsent --limit 20
python -m app.main feedback --id 123 --label linkedin_idea
python -m app.main create-asset --id 123 --type linkedin
```

## Destination routing

Saved signals are routed by source destination first. If a source uses `destination: default`, routing falls back to the analysis category.

Supported destination keys:

```text
default, career, ai_engineering, research, teaching, content, tools, english, global_economy, other
```

Configure category destinations in `.env`:

```env
DESTINATION_CHAT=@praveen_signal_os
DEST_CAREER_CHAT=@praveen_career_radar
DEST_RESEARCH_CHAT=@praveen_research_vault
DEST_TEACHING_CHAT=@praveen_teaching_vault
DEST_CONTENT_CHAT=@praveen_content_ideas
DEST_TOOLS_CHAT=@praveen_tools_to_try
```

Empty destination values fall back to `DESTINATION_CHAT`.

## Option A: use Ollama

```bash
ollama serve
ollama pull qwen3:8b
```

Set this in `.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
```

## Option B: use OpenCode

OpenCode supports non-interactive CLI usage with `opencode run "your prompt"`. The project uses that mode when `LLM_PROVIDER=opencode`.

Set this in `.env`:

```env
LLM_PROVIDER=opencode
OPENCODE_MODEL=
OPENCODE_TIMEOUT_SECONDS=180
```

You can optionally start an OpenCode server to avoid repeated cold starts:

```bash
opencode serve
```

Then set:

```env
OPENCODE_ATTACH_URL=http://localhost:4096
```

## Run the monitor

```bash
python -m app.main monitor
```

The first run will ask you to sign in to Telegram. Telethon creates a local session file. Do not commit that session file.

## Backfill recent messages

The monitor processes only new messages. Use backfill to process recent historical messages from each configured source:

```bash
python -m app.main backfill --limit 20
```

By default, backfill stores useful signals locally but does not forward them to Telegram.

To review locally saved signals that have not yet been sent:

```bash
python -m app.main unsent --limit 20
```

To send those previously saved unsent signals to your destination channel:

```bash
python -m app.main send-unsent --limit 20
```

You can also send saved signals during a backfill:

```bash
python -m app.main backfill --limit 20 --send
```

If you already ran backfill without `--send`, rerunning with `--send` will now also forward saved-but-unsent signals instead of only skipping duplicates.

## Review recent sent saved signals

```bash
python -m app.main recent
```

Or limit the output:

```bash
python -m app.main recent --limit 10
```

## Generate daily briefing

```bash
python -m app.main briefing
```

Optionally send the briefing to Telegram:

```bash
python -m app.main briefing --send
```

## Run tests

```bash
pip install -r requirements-dev.txt
pytest
```

The current tests exercise the local processing pipeline, source registry, source recommendations, feedback storage, asset generation, storage, and model normalization without requiring Telegram, Ollama, or OpenCode.

## Safety and privacy

Use this as a personal knowledge filter, not as a surveillance system.

- Monitor only public channels or groups where you are a legitimate member.
- Do not monitor employer/internal/private chats.
- Do not collect sensitive personal data.
- Keep destination channels private.
- Respect Telegram community rules and local laws.

## MVP decision logic

A message is saved when:

1. It passes basic noise filtering.
2. It is not already stored.
3. The configured LLM/backend returns `is_valuable=true`.
4. Its score is greater than or equal to the source-specific `min_save_score`, or global `MIN_SAVE_SCORE` if the source has no override.

Default threshold: `7.0`.
