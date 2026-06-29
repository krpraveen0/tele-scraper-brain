# Praveen Signal OS

A local-first personal intelligence system that monitors Telegram sources, filters noisy posts, scores useful signals with a local LLM, stores them in SQLite, and sends high-value summaries back to your private Telegram channels.

This MVP focuses on Telegram + Ollama + SQLite.

## What it does

- Monitors selected Telegram channels/groups using Telethon.
- Cleans and deduplicates messages.
- Applies a cheap rule-based pre-filter before using the LLM.
- Uses Ollama/local LLM to classify, summarize, score, and recommend an action.
- Stores every evaluated signal in SQLite.
- Sends useful items to a private Telegram destination.
- Can generate a daily briefing from saved signals.

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
│   ├── config.py
│   ├── daily_briefing.py
│   ├── dedupe.py
│   ├── llm_filter.py
│   ├── main.py
│   ├── message_cleaner.py
│   ├── models.py
│   ├── rule_filter.py
│   ├── storage.py
│   └── telegram_client.py
├── data/
│   └── .gitkeep
├── prompts/
│   └── classify_message.txt
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10+
- Telegram API credentials from https://my.telegram.org
- Ollama running locally
- A private Telegram channel/group where the bot/user client can post saved signals

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with your values.

Start Ollama:

```bash
ollama serve
ollama pull llama3.1:8b
```

## Run the monitor

```bash
python -m app.main monitor
```

The first run will ask you to sign in to Telegram. Telethon creates a local session file. Do not commit that session file.

## Generate daily briefing

```bash
python -m app.main briefing
```

Optionally send the briefing to Telegram:

```bash
python -m app.main briefing --send
```

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
3. The local LLM returns `is_valuable=true`.
4. Its score is greater than or equal to `MIN_SAVE_SCORE`.

Default threshold: `7.0`.
