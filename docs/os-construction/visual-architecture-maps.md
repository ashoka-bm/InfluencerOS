# Visual Architecture Maps

InfluencerOS should maintain visual maps for the overall system and for major pieces before or alongside implementation.

These maps help future agents and humans see what is being built, where each part lives, and how records move through the system.

## Reference Skill

Use this saved mapping skill as the source workflow for architecture maps:

```text
/Users/ashokaji/Documents/Codex/2026-06-29/mcp-servers-excalidraw-url-https-api/outputs/repo-architecture-map/SKILL.md
```

Use this saved Excalidraw API reference when native Excalidraw MCP tools are not visible:

```text
/Users/ashokaji/Documents/Codex/2026-06-29/mcp-servers-excalidraw-url-https-api/outputs/repo-architecture-map/references/excalidraw-api.md
```

## Map Types

Create focused maps instead of one oversized diagram.

| Map type | Use when | Required output |
| --- | --- | --- |
| System architecture map | Showing the full InfluencerOS operating system. | Markdown map plus Excalidraw scene. |
| Workflow map | Showing one end-to-end flow, such as creator setup or content creation. | Input, transformation, output, and gate diagram. |
| Artifact lifecycle map | Showing how records, schemas, examples, and generated artifacts relate. | Source-to-validation diagram. |
| Skill orchestrator map | Showing conductor skills and subskills. | Orchestrator, called skills, handoffs, and stopping gates. |
| Module map | Showing code modules and responsibilities. | Module table plus diagram. |
| Before/after map | Showing a proposed refactor or architecture change. | Current state, target state, and migration handoff. |

## Storage

Store construction maps under:

```text
docs/os-construction/maps/
```

Each map should have a Markdown file:

```text
docs/os-construction/maps/<map-slug>.md
```

The Markdown file should record:

- purpose,
- map type,
- source files inspected,
- Excalidraw scene URL or ID,
- local screenshot path when one exists,
- last visual verification date,
- open questions.

Do not commit generated screenshots unless the user asks. Put disposable screenshot exports in `.tmp/`.

## Required Map Standard

Every architecture map must:

- show a clear reading direction,
- name the primary inputs and outputs,
- show meaningful handoffs instead of every import,
- include source-file references for claims,
- keep high-level diagrams to 6-15 major nodes when possible,
- use separate maps when the system becomes crowded,
- include approval gates and human-in-the-loop stops,
- show local state boundaries and provider boundaries when relevant.

## Excalidraw Rules

When creating an Excalidraw scene:

- create editable shapes, text, and arrows, not a flattened image,
- bind arrows to shapes when supported,
- use short labels,
- use containers only for real boundaries,
- use one dominant reading direction,
- avoid diagonal arrows through unrelated nodes,
- use neutral colors with one accent for the main flow,
- use warning color only for gates, blockers, or approval stops.

When native Excalidraw tools are not available, use the saved API reference and the HTTP MCP endpoint documented there.

Provider or paid calls still require explicit user approval. Creating or editing a diagram through an already-approved Excalidraw connection is allowed when the user asks for a map.

## Verification

A map is not done until it is visually checked.

The agent must:

1. render or screenshot the scene,
2. inspect the image,
3. fix clipped text, overlaps, unreadable labels, bad arrow crossings, and ambiguous labels,
4. verify key labels through scene search or content readback when available,
5. record any renderer caveat in the map Markdown file.

## First Maps To Create

Recommended first map set:

1. Overall InfluencerOS architecture.
2. Creator Workspace and private local state boundary.
3. Creator setup workflow.
4. Content creation pipeline from Creator Profile to Output Package.
5. Skill orchestrator map for `skills/influencer-os/SKILL.md`.
6. Learning OS feedback loop.
7. Agentic OS alignment and divergence gate.

