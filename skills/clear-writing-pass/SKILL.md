---
name: clear-writing-pass
description: "Use on drafted article, thread, caption, or plan text to run the advisory Clear-Writing Pass: a bounded editorial rewrite that removes clutter, filler, and hedging while preserving meaning. Returns rewritten text plus a change trace; writes no record and never blocks."
---

# Clear-Writing Pass

You run an editorial Pass (ADR 0024): a bounded rewrite, not a review.
Follow `docs/gates-and-reviews.md`. You return two things in conversation —
the rewritten text and a change trace — and write no ReviewRecord.

## Edit Discipline

- Remove clutter: filler phrases, redundant qualifiers, throat-clearing
  openers, stacked prepositions, empty intensifiers.
- Prefer concrete verbs and short sentences; keep one idea per sentence.
- Preserve meaning, claims, evidence references, and the piece's spine
  (hook, retain, payoff, CTA) exactly — clarity edits never restructure
  the argument or change what is promised.
- Bounded depth: edit sentences, not sections. If the piece needs
  restructuring, say so as a note instead of doing it.
- Never introduce new claims, examples, or numbers.

## Change Trace

Report what changed so the author can accept or reject each move:

- a short list of edit types applied (e.g. "cut 9 filler phrases",
  "split 4 run-ons"),
- before → after for every edit that changes more than surface wording,
- anything you flagged but deliberately did not touch, and why.

## Boundaries

- No record: Passes emit no ReviewRecord and no file writes — the author
  applies the rewrite to the draft themselves (or asks you to).
- Advisory: the author may reject any or all edits; never present the
  rewrite as required.
- Do not judge hook/payoff quality (that is `review-hook-payoff`) and do
  not fact-check claims (unbuilt review); stay on clarity.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md clear-writing-pass "<lesson>"`.
