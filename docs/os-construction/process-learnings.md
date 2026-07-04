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
- 2026-07-03: Test scaffolds must mirror constructor output, not a convenient approximation. The research scaffold placed projects in id-named folders while `init-project` creates slug-named ones, so the warning-target check's id-folder assumption passed for a layout no constructor produces; slice 5 caught it only because a new check scanned by manifest id. When a scaffold hand-builds what a CLI constructs, build it through the CLI or copy the CLI's layout exactly.
- 2026-07-03: Batch plans should put a skill folder and its registry/context-matrix rows in the same batch — the registry drift checks pin them to one commit, so a "skill first, docs later" split cannot land green. The slice 5 plan split them across batches B and C and had to fold the rows into B.
- 2026-07-03: When the same record type is reachable from more than one CLI command, its checks must live in shared functions called by every path. The queue/research promotion checks accumulated one slice at a time on whichever command was closest, and the paths drifted until the five-slice review reproduced four one-sided bypasses; per-slice reviews audit the slice, not the seams between slices.
- 2026-07-03: Closing a vulnerability class at the validation seam does not close it at the write seam. The slice 1 review added symlink containment to `validate workspace`; the same broken-symlink class stayed open in `import-intake`'s copy until the five-slice review — when a review closes a containment gap, sweep every filesystem write for the same class in the same change.
- 2026-07-03: Verification scripts recorded in progress docs are prose, not pinned — they rot the moment a new at-rest check lands (slice 5's closure check broke the documented queue-before-project ordering silently). Re-run the documented script end to end whenever a slice adds a cross-record check, not only the tests.
- 2026-07-04: Mutator-only invariants are not enough for file-first records. Slice 7's registration command enforced output-package format/project matching, but `validate project` did not, so a hand-edited packaged project validated at rest. Any invariant a writer enforces must also be re-checkable by the standing validator for that record state.
- 2026-07-04: Schema/ADR additions need an inventory-doc sweep after tests pass. The research-intelligence hardening added two schemas and ADR 0021 cleanly, but architecture maps, README, and pipeline-contract counts still described the old record set until a stale-reference scan caught them.
