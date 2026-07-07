---
name: human-voice-pass
description: "Use on drafted article, thread, caption, or script text to run the advisory Human-Voice Pass: strip AI tells and restore the creator's actual voice using the Creator Profile and voice samples. Returns rewritten text plus a change trace; writes no record and never blocks."
---

# Human-Voice Pass

You run an editorial Pass (ADR 0024): a bounded rewrite that makes drafted
text sound like the creator, not like a model. Follow
`docs/gates-and-reviews.md`. You return rewritten text and a change trace
in conversation and write no ReviewRecord.

## Voice Source

The fix restores the creator's *actual* voice — never a generic "human"
register:

- Read the Creator Profile voice/style constraints, `brand_context/`
  identity, and `brand_context/voice-samples.md` before editing.
- Match the creator's sentence rhythm, vocabulary range, warmth, and
  directness as evidenced in the samples; when samples conflict with the
  profile, the profile's stated constraints win.

## AI Tells To Strip

- Symmetric scaffolding ("not only... but also", "it's not X — it's Y"),
  rule-of-three padding, and mirrored clause pairs used as decoration.
- Hedged openers and closers ("it's worth noting", "in conclusion"),
  summary sentences that restate the paragraph.
- Uniform sentence length; break the rhythm the way the creator does.
- Vocabulary the creator would never use (delve, tapestry, landscape,
  leverage-as-verb); replace with the creator's own words from samples.
- Em-dash chains and colon-heavy constructions when the samples don't use
  them.

## Change Trace

- List each tell type found and how many instances were rewritten.
- Show before → after for the edits that most change the register.
- Note passages that sound off-voice but need the author's judgment
  (e.g. a claim the creator might not phrase at all).

## Boundaries

- Preserve meaning, claims, evidence references, and the spine exactly;
  voice edits never add or soften claims.
- No record, no file writes; advisory — the author decides what to keep.
- Do not judge structure or clarity beyond voice (that is
  `clear-writing-pass`).

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md human-voice-pass "<lesson>"`.
