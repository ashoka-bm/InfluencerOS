# Agentic OS Divergence Test

Use this test before changing InfluencerOS architecture, file layout, skill structure, workflow sequencing, memory policy, or approval gates.

Reference repo:

```text
/Users/ashokaji/code/External repos/Agentic Academy/agentic-os
```

## Pass Criteria

A proposed change passes when one of these is true:

- It matches an Agentic OS pattern already listed in `agentic-os-alignment.md`.
- It is an accepted divergence already listed in `agentic-os-alignment.md`.
- It has a new ADR or alignment-doc entry that names the divergence and the user has approved it.

If none of those is true, the change fails.

## Test Steps

1. Name the proposed change in one sentence.
2. Identify the matching Agentic OS reference file or pattern.
3. Identify the InfluencerOS file or pattern being changed.
4. Decide whether the change is a copy, adaptation, or divergence.
5. If it is a divergence, record:
   - what Agentic OS does,
   - what InfluencerOS will do differently,
   - why the difference is needed,
   - whether it is temporary or permanent,
   - where the decision is documented.
6. Stop before implementation if the divergence is not documented and approved.

## Required Output

For any architecture-impacting change, include this block in the implementation note, PRD update, ADR, or issue:

```text
Agentic OS divergence test:
- Proposed change:
- Agentic OS reference:
- InfluencerOS decision:
- Classification: copy | adaptation | divergence
- Decision record:
- Status: pass | blocked
```

## Architecture-Impacting Changes

Run this test for changes to:

- root context files,
- repo layout,
- Creator Workspace layout,
- workflow ordering,
- skill conductor structure,
- skill feedback or learning memory,
- schema boundaries,
- approval gates,
- local versus hosted execution,
- output storage locations.

Do not run this test for small copy edits, typo fixes, example data corrections, or tests that do not change product architecture.
