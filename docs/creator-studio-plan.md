# CTO-002 — Creator Studio Product Plan

Status: Proposed

This document is the formal planning artifact for Creator Studio before feature implementation starts.

## Vision

Current product:

```text
Praveen Signal OS
```

Target direction:

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

## Primary user needs

Praveen needs a daily system to:

- turn saved technical signals into original content ideas
- avoid generic AI-style writing
- create technical blogs and articles
- prepare course modules for teaching
- create written podcast scripts
- create storybook-style tech firm narratives
- manage drafts and content status over time

## Product principles

1. Start from real saved signals, not blank prompts.
2. Keep deterministic generation first; add LLM refinement later.
3. Keep human review before any external posting.
4. Keep creator logic outside Streamlit callbacks.
5. Add quality gates before calling anything ready.
6. Build one thin slice at a time.

## Expert review lenses

### Tech writer lens

Every output should be reader-first and define:

- target reader
- reader pain
- reader promise
- prerequisite knowledge
- practical takeaway
- jargon risk

Recommendation: generate structured blueprints before full drafts.

### Software architect lens

Creator Studio needs a clean domain model, not random generator functions.

Planned modules:

```text
app/idea_lab.py
app/blueprint_generator.py
app/series_builder.py
app/course_factory.py
app/story_studio.py
app/quality_gates.py
app/publishing_queue.py
app/voice_profile.py
```

Recommended flow:

```text
Streamlit UI -> UI services -> creator services -> SQLite -> Markdown export -> optional LLM rewrite
```

### UX designer lens

The UI should guide user intent.

It should ask:

```text
What do you want to create today?
```

Not:

```text
Which CLI command do you remember?
```

Recommended navigation:

```text
Dashboard
Signals Inbox
Creator Studio
Publishing Queue
Briefings
Feedback Profile
Assets
```

### Storyteller lens

Story outputs must include:

- character
- context
- conflict
- decision
- consequence
- transformation
- lesson

Story Studio should be first-class, not only a blog variation.

### Course designer lens

Course outputs must include:

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

## Creator Studio framework

```text
S.I.G.N.A.L -> A.N.G.L.E -> B.L.U.E.P.R.I.N.T -> S.E.R.I.E.S -> P.U.B.L.I.S.H
```

### SIGNAL

Converts a saved signal into thinking material:

- Source
- Insight
- Gap
- Novelty
- Action
- Longevity

### ANGLE

Generates creative directions:

- beginner
- senior engineer
- architect
- founder/product
- teaching
- career
- contrarian
- podcast
- storybook
- course

### BLUEPRINT

Structures an idea before drafting:

- big promise
- lead scene
- unique angle
- example
- practical framework
- reader transformation
- implementation path
- narrative flow
- takeaway

### SERIES

Turns a strong idea into a multi-part arc.

### PUBLISH

Tracks polish, voice, references, diagrams, schedule, history, and reuse.

## Proposed UI

### Creator Studio tab

Creator Studio should contain these sections over time:

```text
Idea Lab
Blueprint Studio
Series Builder
Course Factory
Story Studio
```

### Idea Lab MVP

Controls:

- select saved signal
- generate report
- copy report
- later: save idea
- later: send to Blueprint Studio

Output:

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

### Blueprint Studio MVP

Controls:

- select signal or idea
- choose blueprint type
- generate blueprint
- copy/export blueprint

Blueprint types:

- tech blog
- deep article
- course module
- podcast script
- storybook chapter

### Publishing Queue MVP

Tracks:

- title
- source signal
- content type
- target platform
- status
- priority
- exported path
- published URL

## Data model proposal

Add persistence only after the first Idea Lab and Blueprint flows prove useful.

### ideas

```text
id
signal_id
core_insight
hidden_gap
novel_angle
recommended_format
created_at
```

### idea_angles

```text
id
idea_id
angle_type
title
description
target_audience
score
```

### blueprints

```text
id
idea_id
blueprint_type
title
audience
promise
opening_scene
framework
outline
diagram_idea
quality_score
created_at
```

### publishing_queue

```text
id
blueprint_id
platform
status
priority
scheduled_for
published_url
created_at
updated_at
```

## Quality gates

Every major creator output should answer these questions.

### Originality

- What would a generic AI answer say?
- How is this different?
- What is Praveen's unique angle?

### Technical depth

- Does this show engineering judgment?
- Are trade-offs included?
- Are failure modes included?

### Reader usefulness

- Can the reader apply this tomorrow?
- Is there a clear example?
- Is there a checklist or framework?

### Story strength

- Is there tension?
- Is there a before/after?
- Is there a decision?
- Is there transformation?

### Reusability

- Can this become a blog?
- Can it become a course lesson?
- Can it become a podcast?
- Can it become a story chapter?
- Can it become a LinkedIn post?

## Non-goals for the first implementation

Do not build these first:

- automatic posting
- social scheduling
- full article drafting
- full course builder
- multi-user support
- public deployment
- cloud sync
- payment features

## Roadmap

### Phase 1 — Idea Lab MVP

Tickets:

- CTO-003 Idea Lab deterministic engine
- CTO-004 Idea Lab CLI command
- CTO-005 Creator Studio UI tab

Outcome:

```text
One saved signal can become structured angles and content seeds.
```

### Phase 2 — Blueprint Studio MVP

Tickets:

- CTO-006 Blueprint Generator MVP
- CTO-007 Blueprint UI integration

Outcome:

```text
An idea can become a structured blog/course/podcast/story blueprint.
```

### Phase 3 — Persistence and queue

Tickets:

- CTO-008 Creator persistence design
- CTO-009 Publishing Queue MVP

Outcome:

```text
Ideas and blueprints can be saved and tracked.
```

### Phase 4 — Full Creator Studio

Tickets:

- CTO-010 Series Builder MVP
- CTO-011 Course Factory MVP
- CTO-012 Story Studio MVP

Outcome:

```text
Series, courses, and story scripts become first-class workflows.
```

### Phase 5 — Personalization and quality

Tickets:

- CTO-013 Praveen Voice Profile
- CTO-014 LLM-assisted creative rewrite layer
- CTO-015 Quality Gate Dashboard
- CTO-016 Export and archive workflow
- CTO-017 Final UI simplification pass

Outcome:

```text
The system becomes personalized, quality-controlled, exportable, and easier to use.
```

## Testing strategy

Every implementation ticket must run:

```bash
python -m pytest -q
```

Every UI ticket must also run:

```bash
streamlit run ui/streamlit_app.py
```

Every generator ticket must be deterministic and testable without LLM.

Every storage ticket must test against a temporary SQLite database.

## Start condition for CTO-003

Start CTO-003 only when:

- CTO-001 is merged
- CTO-002 is merged
- tests pass locally
- Streamlit starts locally
- this plan is accepted

## Final recommendation

The first real development ticket after this plan should be:

```text
CTO-003 — Idea Lab deterministic engine
```

CTO-003 should be backend-only and should not touch Streamlit yet.
