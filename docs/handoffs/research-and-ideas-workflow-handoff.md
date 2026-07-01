# Handoff: Research And Ideas Workflow

Date: 2026-06-29
Repo: `/Users/ashokaji/code/fullstock/InfluencerOS`

## Purpose

Use this handoff to start a focused Grill Me With Docs session for the Research and Idea Generation workflow.

The goal is to define the step-by-step research, scraping/browsing, evidence capture, idea generation, and project selection process.

## Current Architecture Context

Research and ideas are part of Phase 1: Planning OS.

Relevant records and schemas:

- `social-research-pack.schema.json`
- `video-understanding-pack.schema.json`
- `content-idea-set.schema.json`
- `selected-content-idea.schema.json`
- `project.schema.json`

Relevant folder locations:

```text
workspace-library/creators/<creator-slug>/
  research/
    social-research-packs/
    video-understanding-packs/
    sources/
  projects/
    <project-id>/
      idea/
      plan/
```

Key docs:

- `docs/pipeline-contract.md`
- `docs/video-understanding-research.md`
- `docs/social-post-formats.md`
- `docs/social-template-library.md`
- `skills/influencer-os/SKILL.md`

## Decisions Already Made

- Research is time-sensitive and must be dated.
- Trend claims must cite sources and stay tied to evidence.
- Real video research creates a Video Understanding Pack before synthesis.
- Idea generation creates exactly five creator-fit visual social ideas.
- The user must explicitly choose the Selected Content Idea.
- A selected idea that moves into production becomes a Project.
- The system is platform-agnostic by default but can carry platform adaptation context later.

## Open Questions For Grilling

- What sources are allowed or preferred for trend research?
- What scraping/browsing rules should agents follow?
- What should be captured from each source before synthesis?
- When is real video understanding required versus optional?
- What video observations are required: hooks, first frames, transcript, retention patterns, formats, templates?
- How do we prevent research from overriding the Creator Profile?
- How should prior creator learnings and performance summaries influence research and idea generation?
- What metadata must transfer from research into Content Idea Sets and Projects?
- What is the quality bar for the five ideas?
- What should trigger asking the user to choose versus recommending one?

## Desired Output Of The Grilling Session

Produce a workflow spec, likely `docs/workflows/research-and-ideas.md`, that defines:

- research inputs,
- source rules,
- browsing/scraping workflow,
- Video Understanding Pack rules,
- Social Research Pack rules,
- idea generation rules,
- selection gate behavior,
- project creation handoff metadata,
- tests or validation expectations.

Update schemas only if the workflow reveals missing required metadata.
