---
name: create-voice-samples
description: "Use to create voice-samples.md: 5-10 gold-standard creator voice examples with source, mode, reason, and confidence."
---

# Create Voice Samples

Create `brand_context/voice-samples.md` from user-provided writing, transcripts, published content, interview answers, or generated foundation drafts.

Use [docs/templates/creator-setup/voice-samples.md](docs/templates/creator-setup/voice-samples.md) as the output shape.

## Purpose

`brand_context/voice-samples.md` gives downstream agents concrete examples without bloating identity, soul, or personal brand files.

## Size Budget

Target 700-1,300 words. Hard maximum 1,700 words unless the user explicitly asks for a long voice bank.

Keep 5-8 samples by default. Use 9-10 only when the creator has materially different modes, such as paid essay, short post, story, comment, video, voiceover, and brand integration.

Each sample should include:

- exact sample text
- why it matters
- voice signal
- content mode
- source
- confidence

Prefer short, high-signal samples over long essays. For long-form sources, excerpt only the minimum needed to capture cadence and structure.

## Extract

Capture 5-10 samples across relevant modes:

- caption
- short post
- reply or comment
- story frame
- video line
- newsletter or article line
- brand integration line, when commercial content is in scope

## Mark Source And Confidence

Two per-sample labels, matching the template:

- Source: where the sample came from — real published or user-written
  material is `user_provided`; LLM drafts awaiting replacement are
  `generated_from_intake` (the file-level Status rolls these up as
  `user_provided | generated_from_intake | mixed`).
- Confidence: `high | medium | low` — how strongly the sample represents
  the creator's actual voice.

## Completion Criteria

Complete when 5-10 samples exist — each with exact text, source, content
mode, why it represents the voice, and confidence — the file stays inside
the size budget, and `validate workspace` reports no voice-sample floor
failures (minimum 5 samples, 200 words). Drafts require user acceptance
before any readiness status changes; validation is not approval.
