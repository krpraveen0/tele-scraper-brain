# Feedback Intelligence Profile

Phase 9 adds a deterministic feedback intelligence profile.

The command reads local SQLite data and summarizes what the user appears to like, ignore, and produce from saved signals.

## Generate profile

```bash
python -m app.main feedback-profile
```

## Increase scan limit

```bash
python -m app.main feedback-profile --limit 500
```

## What it analyzes

The profile uses:

- feedback labels
- saved signal categories
- source titles
- signal tags
- generated assets
- sent/exported asset outcomes

## What it outputs

Sections include:

- Snapshot
- What Praveen likes
- What Praveen ignores
- Source intelligence
- Tag preferences
- Asset outcomes
- Prompt and source tuning suggestions

## Recommended workflow

```bash
python -m app.main unsent --limit 20
python -m app.main feedback --id <signal_id> --label useful
python -m app.main feedback --id <signal_id> --label not_useful --notes "Too generic"
python -m app.main create-asset --id <signal_id> --type linkedin --save --export
python -m app.main feedback-profile
```

## When it becomes useful

The profile is most useful after 30-50 feedback labels.

Before that, treat it as an early signal rather than a stable preference model.

## Why this matters

This is the first step toward making the system Praveen-aware.

It helps answer:

- Which categories does Praveen actually value?
- Which sources are noisy?
- Which tags appear in useful signals?
- Which asset types are being created and sent?
- What should be boosted or penalized in future prompt tuning?
