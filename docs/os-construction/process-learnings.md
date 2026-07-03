# Process Learnings

This file stores repo-level learnings about building InfluencerOS and improving its skills.

Do not store creator performance learnings here. Creator learnings belong in:

```text
workspace-library/creators/<creator-slug>/memory/
```

## Promotion Rule

1. Capture scope-specific feedback in the relevant local context:
   - Creator feedback in the Creator Workspace.
   - InfluencerOS first-party feedback in `context/learnings.md` or this file.
   - Skill-specific local feedback in `SKILL.local.md` when it changes invocation rules.
2. Watch for repeated feedback across projects or creators.
3. Promote only repeatable, general rules into the base skill.
4. Record promoted rules in the skill registry or an ADR when they affect architecture.

## Current Learnings

- InfluencerOS needs both first-party OS persona memory and creator-specific memory.
- Skill feedback must stay scoped until repeated evidence shows it belongs in the core skill.
- 2026-07-03: Fixture-driven "no warnings" tests bless whatever the fixture does not exercise — the slice 3 promotion-gate fixture cited a video pack no test created, so the gap passed as zero warnings. When a validator gains a new ref type, add an unresolvable-fixture probe in the same change.
- 2026-07-03: Deprecation sweeps must grep prose vocabulary, not just schema tokens. The README still taught the five-ideas flow after slice 3's token-based sweep passed; check the flow narrative in README/ARCHITECTURE against CONTEXT.md whenever a pipeline concept is replaced.
- 2026-07-03: Every copy of a closed vocabulary needs a drift pin — schema embeddings, code constants, and test canonicals alike. The slice 3 reviews found the only unpinned enum copies (project schema, then code-level platform and format sets); the drift test now asserts all three layers agree.

