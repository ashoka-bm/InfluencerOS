# ADR 0005: Performance Attribution Model

## Status

Accepted

## Context

The Learning OS should not treat post performance as one undifferentiated score. A post can fail or succeed at different stages:

- the thumbnail or first frame can earn or lose the click,
- the opening seconds can earn or lose the viewer,
- the body can retain or lose attention,
- the payoff can drive or fail to drive completion, saves, shares, comments, follows, or clicks.

If analytics only store total views and engagement, future idea generation cannot tell which creative decision actually worked.

## Decision

Analytics Snapshot records must preserve enough dimensions to support performance attribution.

The normalized analytics model should distinguish:

- **Packaging performance**: impressions, reach, thumbnail or first-frame exposure, click-through rate when available, title or caption variant, thumbnail asset ID.
- **Hook performance**: first-frame pattern, opening hook text or concept, three-second retention, early drop-off, swipe-away or skip signals when available.
- **Body performance**: average view duration, retention curve points, midpoint retention, replay behavior, section-level notes when available.
- **Payoff performance**: completion rate, loop/replay rate, shares, saves, comments, sentiment themes, follows or subscribers.
- **CTA performance**: clicks, profile visits, link clicks, conversion events, opt-ins, purchases, or other declared call-to-action results when available.
- **Context controls**: platform, format, publish time, creator, audience target, topic, content pillar, production format, duration, trend source, and distribution notes.

Raw platform metrics remain inspectable. Distilled creator learnings become the default memory that influences future research, idea generation, scripting, and planning.

## Consequences

- The Learning OS can say what likely worked instead of merely that a post performed well.
- Future content can improve the weak stage rather than copying the whole post blindly.
- Platform metric gaps are expected; unavailable fields must remain null or absent.
- Output Packages and Published Post Records should preserve enough creative metadata to connect performance back to thumbnail, hook, body, payoff, and CTA decisions.
