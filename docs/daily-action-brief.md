# Daily Action Brief

Phase 8 adds a goal-focused daily action brief.

The regular `briefing` command summarizes saved signals by category. The `daily-action-brief` command is more action-oriented. It picks one practical item for each of Praveen's main goals:

- Career move
- AI engineering learning
- Teaching idea
- Content idea
- English practice
- Economy awareness

## Generate locally

```bash
python -m app.main daily-action-brief
```

## Change the lookback window

```bash
python -m app.main daily-action-brief --hours 48
```

## Inspect more saved signals

```bash
python -m app.main daily-action-brief --limit 100
```

## Send to Telegram

```bash
python -m app.main daily-action-brief --send
```

This uses the same briefing destination as the existing `briefing --send` command.

## Recommended morning workflow

```bash
python -m app.main backfill --limit 20
python -m app.main daily-action-brief
python -m app.main feedback --id <signal_id> --label useful
python -m app.main create-asset --id <signal_id> --type linkedin --save --export
```

## How it works

The command is deterministic and local-only. It does not call the LLM.

It reads:

- recent saved signals from SQLite
- recent generated assets
- feedback label summary

Then it builds a compact action plan with suggested next commands.

## Why this matters

This turns Signal OS from a passive signal collector into a daily execution system.

Instead of only asking "what came in?", it answers:

- what should I prepare for career growth?
- what should I learn today?
- what can I teach?
- what can I post?
- what can I practice speaking?
- what economy signal should I understand?
