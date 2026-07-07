---
name: create-voice-samples
description: "Use to create voice-samples.md: 5-10 gold-standard creator voice examples with source, mode, reason, and confidence."
---

# Create Voice Samples

Create `brand_context/voice-samples.md` from user-provided writing, transcripts, published content, interview answers, or generated foundation drafts.

Use [docs/templates/creator-setup/voice-samples.md](../../docs/templates/creator-setup/voice-samples.md) as the output shape.

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

## Mark Confidence

Label each sample:

- `user_provided`: written or approved by the user
- `source_extracted`: extracted from real source material
- `generated_from_intake`: drafted by the LLM and awaiting replacement

## Completion Criteria

Complete when each sample has exact text, source/context, content mode, why it represents the voice, and confidence.
