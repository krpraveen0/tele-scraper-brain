# Praveen Signal OS Implementation Plan

## Mission

Build a local-first personal AI signal hub that monitors information sources, filters noise, converts useful signals into personal assets, and sends one clear daily action plan.

## MVP scope

### Inputs

- Telegram public channels and groups where the user is a legitimate member.

### Processing

- Clean message text.
- Skip obvious noise.
- Deduplicate by source/message ID and normalized content hash.
- Analyze with local Ollama model.
- Score against personal priorities.

### Storage

- SQLite database under `data/signals.db`.

### Outputs

- Private Telegram destination for saved signals.
- Daily briefing message.

## Persona scoring dimensions

- Career relevance.
- AI engineering relevance.
- Teaching usefulness.
- Content potential.
- Spoken English usefulness.
- Research depth.
- Urgency.
- Noise risk.

## Categories

- Career
- AI Engineering
- Teaching
- Content
- English
- Research
- Tools
- Global Economy
- Other

## Suggested actions

- Read today
- Read weekend
- Apply
- Prepare resume
- Create LinkedIn post
- Create Medium outline
- Use in class
- Create diagram
- Practice speaking
- Try tool
- Archive
- Ignore

## Version 1 checklist

- [x] Repository initialization.
- [x] Environment template.
- [x] Telegram source ingestion.
- [x] Message cleaning.
- [x] Rule-based pre-filter.
- [x] Ollama analysis layer.
- [x] SQLite storage.
- [x] Telegram saved-signal output.
- [x] Daily briefing generation.

## Version 2 roadmap

- Add multiple destination channel routing by category.
- Add source registry with trust scores.
- Add weekly review command.
- Add company watchlist for remote roles.
- Add job-fit scoring prompts.
- Add teaching asset generator.
- Add LinkedIn/Medium idea generator.
- Add embeddings and semantic search.

## Version 3 roadmap

- Add Gmail job-alert ingestion.
- Add RSS/blog ingestion.
- Add GitHub trending/repo monitoring.
- Add arXiv/paper tracking.
- Add local dashboard.
- Add voice-note based English speaking practice.
- Add Notion/Google Drive export.

## Safety rules

- Do not monitor employer/internal chats.
- Do not collect sensitive personal conversations.
- Do not forward private group messages into public destinations.
- Respect Telegram group rules and local laws.
- Keep all generated archives private by default.
