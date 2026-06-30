# Enhanced Asset Workflow

Phase 7.1 extends asset generation with four capabilities:

- Optional LLM rewriting
- SQLite asset history
- Markdown export
- Telegram sending

## Create a basic asset

First list saved signal IDs:

```bash
python -m app.main unsent --limit 20
python -m app.main recent --limit 20
```

Then generate an asset:

```bash
python -m app.main create-asset --id 123 --type linkedin
```

Supported types:

```text
career_note
english_practice
linkedin
medium_outline
research_note
teaching_example
tool_review
```

## Save asset history

```bash
python -m app.main create-asset --id 123 --type linkedin --save
python -m app.main assets --limit 20
```

Saved assets are stored in the local SQLite database in the `assets` table.

## Rewrite with the configured LLM backend

```bash
python -m app.main create-asset --id 123 --type linkedin --rewrite
```

The rewrite uses the existing `LLM_PROVIDER` setting. Supported backends are the same as the filtering pipeline:

```text
ollama
opencode
```

The LLM receives the original saved signal and the deterministic draft, then returns polished Markdown.

## Export to Markdown

```bash
python -m app.main create-asset --id 123 --type teaching_example --export
```

A Markdown file is written to the configured export directory. By default this is:

```text
assets/
```

You can override the target directory:

```bash
python -m app.main create-asset --id 123 --type teaching_example --export --export-dir assets/teaching
```

## Send asset to Telegram

```bash
python -m app.main create-asset --id 123 --type career_note --send
```

Sending also saves the asset to SQLite first so the send status can be tracked.

## Full workflow

```bash
python -m app.main unsent --limit 20
python -m app.main feedback --id 123 --label linkedin_idea
python -m app.main create-asset --id 123 --type linkedin --rewrite --save --export --send
python -m app.main assets --limit 20
```

## Optional environment settings

```env
ASSET_CHAT=your_asset_destination
ASSET_EXPORT_DIR=assets
```

If `ASSET_CHAT` is empty, assets are sent to the default destination channel. If `ASSET_EXPORT_DIR` is empty, exports use the local `assets/` folder.
