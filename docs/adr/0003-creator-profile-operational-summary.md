# ADR 0003: Creator Profile As Operational Summary

## Status

Accepted

## Context

InfluencerOS needs a typed Creator Profile for automation. It also needs richer creator files for biography, psychology, brand strategy, and reference assets.

Three options were considered:

- a minimal pointer record,
- an operational summary,
- a full structured model of every creator detail.

A minimal pointer record would force agents to read every markdown file for routine work. A full structured model would turn nuanced identity and psychology into brittle schema maintenance.

## Decision

`creator-profile.json` will be an operational summary.

It should contain enough structured information for routine research, idea generation, scripting, planning, and output packaging without requiring every workflow to open every markdown file. It should not try to represent the complete identity file, soul file, personal brand file, or reference library inline.

The Creator Profile may include:

- stable creator IDs and display names,
- niche and audience,
- creator positioning,
- voice and persona summary,
- core content pillars,
- hard boundaries and disclosure rules,
- visual identity summary,
- platform or format posture when needed,
- goals,
- pointers to richer workspace files and reference assets.

## Consequences

- Automation gets predictable structured input.
- Rich identity work remains readable in markdown.
- The schema can evolve conservatively around fields that workflows actually need.
- Workflows may open the richer files when nuance, contradiction checks, or high-stakes content decisions require them.
