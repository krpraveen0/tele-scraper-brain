# Praveen Thought OS — Jira-Style Development Roadmap

This file is the step-by-step source of truth for future development.

The goal is to avoid branching confusion, feature overload, and broken incremental releases. Every ticket below must be implemented in order unless explicitly marked as parallel-safe.

## Non-negotiable development rules

### Branching rule

Use exactly one branch per ticket.

Branch naming format:

```bash
feature/<ticket-key-lowercase>-short-name
```

Example:

```bash
feature/cto-001-cleanup-baseline
feature/cto-002-creator-studio-plan
feature/cto-003-idea-lab-engine
```

Do not create retry branches such as `final`, `final2`, `implementation3`, or `real4`.

If a branch is wrong, delete it locally and remotely before creating a corrected branch.

### Development gate rule

Before starting any ticket, the developer must verify the previous version is healthy.

Required pre-start commands:

```bash
git checkout master
git pull
python -m pytest -q
python -m app.main feedback-summary
streamlit run ui/streamlit_app.py
```

The Streamlit command must at least start without import/runtime failure. Manual UI smoke testing must be performed in the browser.

### Bug gate rule

Do not start a new feature ticket if:

- tests are failing
- Streamlit does not start
- an existing CLI command crashes
- the previous feature was merged but not pulled locally
- the previous feature has an unresolved regression

Create a bug ticket first and fix it before moving forward.

### Pull request rule

Every feature ticket should have:

- one branch
- one PR
- clear summary
- test evidence
- screenshots or UI notes when UI changes are included
- no unrelated cleanup

### Merge rule

Merge only after:

- automated tests pass
- local smoke test passes
- at least one manual UI flow is tested when relevant
- acceptance criteria are checked off

---

# Product direction

Current product:

```text
Praveen Signal OS
```

Next product direction:

```text
Praveen Thought OS
```

Purpose:

```text
Convert daily technical signals into original blogs, deep articles, course modules, written podcast scripts, storybook chapters, LinkedIn series, and reusable teaching material.
```

Core workflow:

```text
Signals -> Ideas -> Angles -> Blueprints -> Drafts -> Series -> Publishing Queue
```

---

# Epic CTO: Creator Thought OS

## Epic goal

Build a structured creator system that helps Praveen turn technical signals into differentiated technical content.

## Success criteria

The system should help answer:

- What should I write today?
- What is the non-obvious angle?
- Can this become a blog, course, podcast, or story chapter?
- What is the blueprint?
- What is waiting in my publishing queue?
- What content should I polish next?

---

# Ticket CTO-001 — Baseline cleanup and health check

## Type

Engineering hygiene

## Goal

Establish a clean baseline before Creator Studio development starts.

## Why this ticket exists

Previous development accidentally created many empty branches and some UI changes were patched directly. Before building more, the project must have a known-good baseline.

## Scope

- Pull latest `master`.
- Run full test suite.
- Start Streamlit UI.
- Verify current CLI commands still work.
- Document any known issues.
- Do not add new features.

## Pre-start gate

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

Start this ticket only if the commands above are understood and reproducible.

## Implementation tasks

- [ ] Create branch `feature/cto-001-cleanup-baseline`.
- [ ] Confirm all tests pass.
- [ ] Confirm Streamlit starts.
- [ ] Test Signals Inbox manually.
- [ ] Test quick feedback button manually.
- [ ] Test quick asset generation manually.
- [ ] Create `docs/current-health-check.md` with the test result.

## Acceptance criteria

- [ ] `pytest -q` passes.
- [ ] Streamlit opens without `ModuleNotFoundError`.
- [ ] Signals Inbox loads.
- [ ] Existing `feedback-profile` command still works.
- [ ] Existing `create-asset` command still works.
- [ ] Known issues are documented.

## Test plan

```bash
python -m pytest -q
python -m app.main feedback-summary
python -m app.main assets --limit 5
streamlit run ui/streamlit_app.py
```

## Do not start next ticket if

- any test fails
- UI fails to start
- imports fail
- database migrations break existing data

---

# Ticket CTO-002 — Creator Studio product plan document

## Type

Product planning

## Goal

Create a formal planning document for Creator Studio before implementation.

## Scope

Create:

```text
docs/creator-studio-plan.md
```

The document must include:

- product vision
- user workflow
- expert review lenses
- data model proposal
- UI proposal
- quality gates
- implementation roadmap
- non-goals

## Pre-start gate

CTO-001 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-002-creator-studio-plan`.
- [ ] Add `docs/creator-studio-plan.md`.
- [ ] Include framework: Signals -> Ideas -> Angles -> Blueprints -> Drafts -> Series -> Publishing Queue.
- [ ] Include expert review sections: tech writer, architect, UX designer, storyteller, course designer.
- [ ] Include phased delivery plan.
- [ ] Include testing gates for each future phase.

## Acceptance criteria

- [ ] Plan document exists.
- [ ] Plan is readable as a product roadmap.
- [ ] Plan contains explicit non-goals.
- [ ] Plan prevents building too many features at once.
- [ ] No code behavior changes are included.

## Test plan

```bash
python -m pytest -q
```

Manual review:

- [ ] Read the plan from top to bottom.
- [ ] Confirm each future phase has a clear scope.

## Do not start next ticket if

- plan is vague
- plan mixes development and product decisions unclearly
- plan does not include testing gates

---

# Ticket CTO-003 — Idea Lab deterministic engine

## Type

Backend feature

## Goal

Create the first Creator Studio engine: Idea Lab.

Idea Lab converts one saved signal into structured creative thinking output.

## Scope

Create:

```text
app/idea_lab.py
tests/test_idea_lab.py
```

## Inputs

A `StoredSignal` object.

## Output

A deterministic `IdeaLabReport` containing:

- signal id
- source
- category
- core insight
- hidden gap
- novel angle
- 10 content angles
- title ideas
- diagram ideas
- blog seed
- course seed
- podcast seed
- storybook seed
- quality checklist

## Pre-start gate

CTO-002 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-003-idea-lab-engine`.
- [ ] Add dataclasses: `ContentAngle`, `IdeaSeed`, `IdeaLabReport`.
- [ ] Add `generate_idea_lab_report(signal: StoredSignal) -> IdeaLabReport`.
- [ ] Add `render()` method for Markdown output.
- [ ] Use deterministic templates first.
- [ ] Do not call LLM in this ticket.
- [ ] Add unit tests.

## Acceptance criteria

- [ ] Idea Lab works without network and without LLM.
- [ ] It produces at least 10 angles.
- [ ] It produces blog/course/podcast/storybook seeds.
- [ ] It includes quality checklist.
- [ ] Markdown render is readable.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest tests/test_idea_lab.py -q
python -m pytest -q
```

## Do not start next ticket if

- Idea Lab output is generic and unusable
- test coverage is missing
- report render is unreadable

---

# Ticket CTO-004 — Idea Lab CLI command

## Type

CLI feature

## Goal

Expose Idea Lab through CLI for repeatable local use and testing.

## Scope

Update:

```text
app/main.py
```

Add command:

```bash
python -m app.main idea-lab --id 123
```

Optional:

```bash
python -m app.main idea-lab --id 123 --export
```

## Pre-start gate

CTO-003 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
python -m app.main feedback-summary
```

## Implementation tasks

- [ ] Create branch `feature/cto-004-idea-lab-cli`.
- [ ] Add `run_idea_lab(signal_id: int)`.
- [ ] Add parser command.
- [ ] Validate signal id.
- [ ] Print Markdown report.
- [ ] Add tests if CLI tests already exist, otherwise add lightweight function-level tests.

## Acceptance criteria

- [ ] Invalid signal id gives clear error.
- [ ] Valid signal id prints Idea Lab report.
- [ ] Command does not require Streamlit.
- [ ] Existing commands still work.

## Test plan

```bash
python -m pytest -q
python -m app.main idea-lab --id <existing_signal_id>
```

Manual test:

- [ ] Try one valid signal.
- [ ] Try one invalid signal.

## Do not start next ticket if

- CLI breaks existing parser commands
- output is not useful in terminal

---

# Ticket CTO-005 — Creator Studio UI tab

## Type

UI feature

## Goal

Add Creator Studio to Streamlit and expose Idea Lab inside it.

## Scope

Update:

```text
ui/streamlit_app.py
app/ui_services.py
```

Add top-level tab:

```text
Creator Studio
```

Inside it, add first section:

```text
Idea Lab
```

## Pre-start gate

CTO-004 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
python -m app.main idea-lab --id <existing_signal_id>
```

## Implementation tasks

- [ ] Create branch `feature/cto-005-creator-studio-ui`.
- [ ] Add Creator Studio tab.
- [ ] Let user select a saved signal.
- [ ] Add button: Generate Idea Lab Report.
- [ ] Render report in Markdown.
- [ ] Keep UI simple.
- [ ] Do not add Series Builder yet.
- [ ] Do not add Course Factory yet.

## Acceptance criteria

- [ ] Streamlit starts.
- [ ] Creator Studio tab appears.
- [ ] User can select signal.
- [ ] User can generate report.
- [ ] Existing tabs still work.
- [ ] No import path regression.

## Test plan

```bash
python -m pytest -q
streamlit run ui/streamlit_app.py
```

Manual UI smoke test:

- [ ] Dashboard loads.
- [ ] Signals Inbox loads.
- [ ] Creator Studio loads.
- [ ] Idea Lab report renders.
- [ ] Asset Studio still works.

## Do not start next ticket if

- UI becomes cluttered
- Creator Studio is hard to find
- Signals Inbox breaks

---

# Ticket CTO-006 — Blueprint Generator MVP

## Type

Backend feature

## Goal

Convert an Idea Lab report into structured blueprints.

## Scope

Create:

```text
app/blueprint_generator.py
tests/test_blueprint_generator.py
```

Supported blueprint types:

- tech blog
- deep article
- course module
- podcast script
- storybook chapter

## Pre-start gate

CTO-005 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-006-blueprint-generator`.
- [ ] Add `Blueprint` dataclass.
- [ ] Add blueprint type constants.
- [ ] Add deterministic blueprint generator.
- [ ] Add quality checklist.
- [ ] Add tests.

## Acceptance criteria

- [ ] Generates structured blueprint for each supported type.
- [ ] Includes title, audience, promise, opening, framework, sections, diagram idea, conclusion.
- [ ] Does not call LLM yet.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest tests/test_blueprint_generator.py -q
python -m pytest -q
```

## Do not start next ticket if

- blueprint output is too shallow
- blueprint lacks reader promise
- blueprint lacks practical framework

---

# Ticket CTO-007 — Blueprint UI integration

## Type

UI feature

## Goal

Add Blueprint Studio inside Creator Studio.

## Scope

Update:

```text
ui/streamlit_app.py
app/ui_services.py
```

Add section:

```text
Creator Studio -> Blueprint Studio
```

## Pre-start gate

CTO-006 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-007-blueprint-ui`.
- [ ] Add blueprint type selector.
- [ ] Select signal or Idea Lab report.
- [ ] Generate blueprint.
- [ ] Render Markdown.
- [ ] Add export option only if existing export helpers can be reused safely.

## Acceptance criteria

- [ ] UI generates blueprints.
- [ ] Existing Idea Lab UI still works.
- [ ] Existing Asset Studio still works.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest -q
streamlit run ui/streamlit_app.py
```

Manual test:

- [ ] Generate tech blog blueprint.
- [ ] Generate course module blueprint.
- [ ] Generate storybook chapter blueprint.

## Do not start next ticket if

- Blueprint UI duplicates Idea Lab confusingly
- generated blueprint cannot be copied/exported

---

# Ticket CTO-008 — Creator persistence design

## Type

Architecture and storage

## Goal

Design and add persistence for creator artifacts.

## Scope

Add tables only after Idea Lab and Blueprint flows prove useful.

Proposed tables:

```text
ideas
idea_angles
blueprints
```

## Pre-start gate

CTO-007 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-008-creator-persistence`.
- [ ] Update storage schema.
- [ ] Add migration-safe `CREATE TABLE IF NOT EXISTS` statements.
- [ ] Add save/list/get methods.
- [ ] Add tests with temp SQLite DB.
- [ ] Do not alter existing signals/assets/feedback behavior.

## Acceptance criteria

- [ ] Existing DB opens without migration failure.
- [ ] Existing tests pass.
- [ ] New creator artifact tests pass.
- [ ] Saving Idea Lab report works.
- [ ] Saving blueprint works.

## Test plan

```bash
python -m pytest tests/test_storage*.py -q
python -m pytest -q
```

## Do not start next ticket if

- schema change breaks existing DB
- existing storage tests fail

---

# Ticket CTO-009 — Publishing Queue MVP

## Type

Workflow feature

## Goal

Track content from idea to published output.

## Scope

Add publishing queue model and UI.

Statuses:

- idea captured
- blueprint generated
- draft started
- needs diagram
- needs references
- ready to polish
- ready to publish
- published
- repurpose later

## Pre-start gate

CTO-008 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-009-publishing-queue`.
- [ ] Add queue table.
- [ ] Add queue service.
- [ ] Add UI tab: Publishing Queue.
- [ ] Add status update action.
- [ ] Add platform field: LinkedIn, Medium, Course, Podcast, Storybook.

## Acceptance criteria

- [ ] User can add item to queue.
- [ ] User can update status.
- [ ] User can filter by platform/status.
- [ ] No auto-publishing.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Do not start next ticket if

- queue loses track of source signal
- status update is confusing

---

# Ticket CTO-010 — Series Builder MVP

## Type

Creator feature

## Goal

Convert one topic into a multi-part content series.

## Scope

Supported series types:

- 7-day LinkedIn series
- 5-part Medium series
- 4-episode podcast series
- 6-module course
- 10-chapter tech storybook

## Pre-start gate

CTO-009 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-010-series-builder`.
- [ ] Add `app/series_builder.py`.
- [ ] Add tests.
- [ ] Add UI section.
- [ ] Add export to Markdown.

## Acceptance criteria

- [ ] Series has clear arc.
- [ ] Each part has purpose.
- [ ] Series can be added to publishing queue.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest tests/test_series_builder.py -q
python -m pytest -q
```

## Do not start next ticket if

- series feels like random title list
- no reader journey exists

---

# Ticket CTO-011 — Course Factory MVP

## Type

Teaching feature

## Goal

Turn technical signals and ideas into teachable course modules.

## Scope

Generate:

- module title
- learning outcome
- prerequisite
- explanation
- visual analogy
- demo
- hands-on task
- mini-project
- common mistakes
- assessment questions
- trainer notes

## Pre-start gate

CTO-010 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-011-course-factory`.
- [ ] Add `app/course_factory.py`.
- [ ] Add tests.
- [ ] Add UI section.
- [ ] Add export to Markdown.

## Acceptance criteria

- [ ] Course module is teachable.
- [ ] Includes learner confusion and assessment.
- [ ] Includes trainer notes.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest tests/test_course_factory.py -q
python -m pytest -q
```

## Do not start next ticket if

- output is only an article outline
- learner outcome is unclear

---

# Ticket CTO-012 — Story Studio MVP

## Type

Storytelling feature

## Goal

Create written podcast scripts and tech-firm storybook chapters.

## Scope

Supported formats:

- solo podcast script
- interview-style podcast
- founder-engineer dialogue
- student-teacher dialogue
- tech firm story chapter
- debugging story
- architecture decision story

## Pre-start gate

CTO-011 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-012-story-studio`.
- [ ] Add `app/story_studio.py`.
- [ ] Add tests.
- [ ] Add UI section.
- [ ] Add quality gate: character, conflict, decision, consequence, lesson.

## Acceptance criteria

- [ ] Story has character and conflict.
- [ ] Story has technical decision.
- [ ] Story has lesson.
- [ ] Podcast scripts are readable aloud.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest tests/test_story_studio.py -q
python -m pytest -q
```

## Do not start next ticket if

- story output is technically correct but emotionally flat
- podcast script does not sound human

---

# Ticket CTO-013 — Praveen Voice Profile

## Type

Personalization feature

## Goal

Create a profile that helps the system avoid generic AI-style output.

## Scope

Capture preferences for:

- tone
- writing style
- preferred openings
- disliked phrases
- technical depth
- examples
- storytelling style
- content formats

## Pre-start gate

CTO-012 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-013-voice-profile`.
- [ ] Add `app/voice_profile.py`.
- [ ] Add profile storage.
- [ ] Add UI editor.
- [ ] Use profile in future LLM rewrite prompts.

## Acceptance criteria

- [ ] User can view and edit voice profile.
- [ ] Profile can be used by content generators.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Do not start next ticket if

- profile is too vague
- profile cannot be applied to generated outputs

---

# Ticket CTO-014 — LLM-assisted creative rewrite layer

## Type

LLM enhancement

## Goal

Add optional LLM improvement after deterministic outputs are stable.

## Scope

Use configured LLM backend to improve:

- Idea Lab angles
- blueprints
- story scripts
- course explanations
- titles
- hooks

## Pre-start gate

CTO-013 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-014-llm-creative-rewrite`.
- [ ] Add prompt templates.
- [ ] Add safe fallback if LLM is unavailable.
- [ ] Add tests using fake LLM.
- [ ] Add UI toggle: Improve with LLM.

## Acceptance criteria

- [ ] Deterministic mode still works without LLM.
- [ ] LLM failures are handled gracefully.
- [ ] Rewritten output respects voice profile.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest -q
```

Manual test:

- [ ] Run with LLM available.
- [ ] Run with LLM unavailable.

## Do not start next ticket if

- deterministic mode breaks
- LLM errors crash UI

---

# Ticket CTO-015 — Quality Gate Dashboard

## Type

Quality feature

## Goal

Evaluate whether generated content is original, useful, technically deep, story-driven, and reusable.

## Scope

Add quality scoring for:

- originality
- reader usefulness
- technical depth
- story strength
- reusability

## Pre-start gate

CTO-014 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-015-quality-gates`.
- [ ] Add `app/quality_gates.py`.
- [ ] Add tests.
- [ ] Add UI quality checklist.
- [ ] Add recommendation messages.

## Acceptance criteria

- [ ] Quality report is shown before publishing.
- [ ] Weak content is flagged.
- [ ] Suggestions are actionable.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest tests/test_quality_gates.py -q
python -m pytest -q
```

## Do not start next ticket if

- quality gates become vague
- score does not explain how to improve

---

# Ticket CTO-016 — Export and archive workflow

## Type

Workflow feature

## Goal

Export generated work into organized Markdown folders.

## Scope

Export folders:

```text
exports/blogs
exports/articles
exports/courses
exports/podcasts
exports/storybook
exports/linkedin
exports/series
```

## Pre-start gate

CTO-015 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-016-export-archive`.
- [ ] Add export helpers.
- [ ] Add UI export buttons.
- [ ] Add metadata frontmatter.
- [ ] Add tests.

## Acceptance criteria

- [ ] Exports are organized by type.
- [ ] Markdown files include metadata.
- [ ] Existing asset exports still work.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest -q
```

Manual test:

- [ ] Export one blog blueprint.
- [ ] Export one course module.
- [ ] Export one story chapter.

## Do not start next ticket if

- export paths are inconsistent
- files overwrite each other accidentally

---

# Ticket CTO-017 — Final UI simplification pass

## Type

UX polish

## Goal

Reduce UI complexity after features are added.

## Scope

Review and simplify:

- Dashboard
- Signals Inbox
- Creator Studio
- Publishing Queue
- Assets
- Feedback Profile

## Pre-start gate

CTO-016 must be merged and verified.

Run:

```bash
git checkout master
git pull
python -m pytest -q
streamlit run ui/streamlit_app.py
```

## Implementation tasks

- [ ] Create branch `feature/cto-017-ui-simplification`.
- [ ] Remove duplicate actions.
- [ ] Group actions by user intent.
- [ ] Add helper text.
- [ ] Reduce button overload.
- [ ] Improve empty states.

## Acceptance criteria

- [ ] User can understand what to do next from Dashboard.
- [ ] Creator Studio is not overwhelming.
- [ ] No duplicate confusing actions.
- [ ] Streamlit starts cleanly.
- [ ] Tests pass.

## Test plan

```bash
python -m pytest -q
streamlit run ui/streamlit_app.py
```

Manual review:

- [ ] Open app as a new user.
- [ ] Identify next action in under 10 seconds.
- [ ] Generate an Idea Lab report.
- [ ] Generate a blueprint.
- [ ] Add one item to Publishing Queue.

---

# Release milestones

## Milestone 1 — Stable current app

Tickets:

- CTO-001
- CTO-002

Outcome:

```text
Clean baseline and clear plan.
```

## Milestone 2 — Idea Lab MVP

Tickets:

- CTO-003
- CTO-004
- CTO-005

Outcome:

```text
One signal can become multiple original content angles from CLI and UI.
```

## Milestone 3 — Blueprint Studio

Tickets:

- CTO-006
- CTO-007

Outcome:

```text
An idea can become a structured blog/course/podcast/story blueprint.
```

## Milestone 4 — Persistence and publishing workflow

Tickets:

- CTO-008
- CTO-009

Outcome:

```text
Ideas and blueprints can be saved and tracked.
```

## Milestone 5 — Full Creator Studio

Tickets:

- CTO-010
- CTO-011
- CTO-012

Outcome:

```text
Series, courses, and story scripts become first-class workflows.
```

## Milestone 6 — Personalization and polish

Tickets:

- CTO-013
- CTO-014
- CTO-015
- CTO-016
- CTO-017

Outcome:

```text
The system becomes personalized, quality-controlled, exportable, and easier to use.
```

---

# Stop conditions

Stop development and create a bug ticket if:

- tests fail on master
- Streamlit fails to start
- a command used in the previous ticket breaks
- SQLite migration affects existing data
- UI becomes harder to use than CLI
- generated content becomes generic or low-quality

---

# Current next action

Start with:

```text
CTO-001 — Baseline cleanup and health check
```

Do not start Creator Studio implementation until CTO-001 and CTO-002 are complete.
