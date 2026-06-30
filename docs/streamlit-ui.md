# Streamlit UI MVP

Phase 10 adds a local Streamlit dashboard so you do not need to remember every CLI command and flag.

## Run the UI

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run ui/streamlit_app.py
```

The UI uses the same `.env`, SQLite database, `sources.yaml`, Telegram session, and local LLM settings as the CLI.

## Pages

The first UI is a single Streamlit app with tabs:

1. Dashboard
2. Signals Inbox
3. Asset Studio
4. Briefings
5. Feedback Profile
6. Assets

## Dashboard

Shows quick metrics:

- total signals
- valuable signals
- unsent signals
- generated assets
- feedback labels
- top categories
- top sources

## Signals Inbox

Use this instead of remembering:

```bash
python -m app.main unsent --limit 20
python -m app.main recent --limit 20
python -m app.main feedback --id 123 --label useful
```

The page supports:

- Unsent / Recent sent / All views
- score filter
- category filter
- signal preview
- original message preview
- feedback label form

## Asset Studio

Use this instead of remembering:

```bash
python -m app.main create-asset --id 123 --type linkedin --save --export
```

The page supports:

- selecting a saved signal
- selecting asset type
- optional LLM rewrite
- optional SQLite save
- optional Markdown export
- asset preview

## Briefings

Use this instead of remembering:

```bash
python -m app.main daily-action-brief --hours 24 --limit 60
python -m app.main daily-action-brief --send
```

The page supports:

- lookback window
- signal limit
- generate daily action brief
- send brief to Telegram

## Feedback Profile

Use this instead of remembering:

```bash
python -m app.main feedback-profile --limit 200
```

The page shows your preference profile based on local feedback labels.

## Assets

Use this instead of remembering:

```bash
python -m app.main assets --limit 20
```

The page supports:

- asset history table
- asset preview
- send asset to Telegram

## Important notes

This is a local personal dashboard. Do not expose it publicly.

For the MVP, long-running operations like continuous Telegram monitoring are still better run from the CLI or a separate process. The UI focuses on review, feedback, asset generation, briefings, and lightweight sending.
