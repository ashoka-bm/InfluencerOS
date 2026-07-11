# Agentic OS Alignment

InfluencerOS should copy the Agentic OS architecture where it fits and adapt it only by explicit decision.

Reference source:

```text
/Users/ashokaji/code/External repos/Agentic Academy/agentic-os
```

## Alignment Rule

When a proposed architecture, workflow, file layout, or skill pattern differs from the Agentic OS reference, the agent must stop and name the divergence before implementing it.

The note must include:

- what Agentic OS does,
- what InfluencerOS would do differently,
- why the difference is needed,
- whether the difference is temporary or permanent,
- the document or ADR that records the decision.

## Adopted Patterns

| Agentic OS pattern | InfluencerOS adaptation | Status |
| --- | --- | --- |
| Thin root adapters load durable context. | `AGENTS.md` is canonical; `CLAUDE.md` and root `SOUL.md` are thin wrappers that import it; the read order is defined once in `AGENTS.md` and drift-checked. | Adopted; enforced in ADR 0019 |
| Shared rules live in stable standards files. | Product rules live in `AGENTS.md`, `CONTEXT.md`, `ARCHITECTURE.md`, and `docs/os-construction/`. | Adopted |
| Static context is separate from dynamic memory. | Repo docs hold static product context; root `context/` holds first-party OS persona memory; Creator Workspaces hold creator-specific context, memory, research, projects, and progress. | Adopted |
| Root system can act as its own persona/client. | Root `context/` and `brand_context/` hold first-party InfluencerOS persona context; Creator Workspaces hold creator-specific context. | Adopted |
| Skills stay modular and load extra context only when needed. | `skills/` contains conductor and creator-setup skills; future skills should use progressive disclosure. | Adopted |
| Workflows chain modular skills through an orchestrator. | Conductor skills declare a `## Dependencies` table and a phase-to-owner map with explicit `Skill(skill: "...")` calls (ADR 0017); `skills/influencer-os/SKILL.md` is the content conductor and `skills/create-influencer/SKILL.md` the setup conductor. | Adopted; formalized in ADR 0017 |
| Outputs live in predictable project folders. | Creator outputs live under `workspace-library/creators/<creator-slug>/projects/<project-id>/`. | Adopted |
| System skills improve themselves from feedback. | `wrap-up` and `memory-write` system skills write `context/learnings.md`, `process-learnings.md`, `SKILL.local.md`, and `context/MEMORY.md`; behavior skills carry `## Rules`/`## Self-Update`. | Accepted in ADR 0016 |
| External tools plug in through explicit skill/tool boundaries without vendoring. | `bradautomates/claude-video` `/watch` is an optional external acquisition tool for Video Understanding Packs; it stays outside the repo, out of conductor `dependencies`, and inside the provider boundary (decision record in `docs/video-understanding-research.md`, tracked in the skill-registry External Tool Integrations table). | Adopted (2026-07-03) |
| Creator performance learning feeds future ideas. | Learning OS records analytics, performance summaries, and distilled creator memory (`distill-creator-learning`) before future ideas use those lessons. | Contracted (Phase 2) |
| Engagement-weighted, cross-validated synthesis judges what is worth using. | The Signal Tier Rubric anchors `visible_metric_signal` and `confidence`, and the Synthesis Discipline requires corroboration breadth plus a contradiction pass (`docs/workflows/research-and-ideas.md`); both adapt `str-trending-research`'s `synthesis-guide.md` and `score.py` into agent-authored, creator-relative, no-formula guidance over the ADR 0021 schemas. The weighted-sum score and batch normalization are deliberately not imported. | Adopted (2026-07-04); adapts ADR 0021 |
| Benchmark-anchored analytics interpretation with stage remediation. | The Performance Benchmark Rubric (CTR/retention/engagement bands) and the metric-to-remediation mapping in `skills/create-performance-summary/SKILL.md` adapt the reference `mkt-content-analytics` skill's benchmarks and optimization playbook onto the five InfluencerOS attribution stages, anchoring `stage_findings` and `recommended_next_actions` to a closed rubric the way the Signal Tier Rubric anchors research confidence; bands are creator-relative once a baseline exists, and unanchored ADR 0020 platforms are judged only against recorded creator baselines. | Adopted (2026-07-05); Phase 2 slice 3 |
| Hybrid semantic memory, phased: keyword leg now, vector leg with Command Centre. | The reference's memory search is hybrid by design (vector + keyword legs fused with RRF, then a three-stage rerank) inside the Command Centre (`command-centre/src/lib/memory/`). Phase 2 slice 6 builds the keyword leg as a SQLite FTS5 projection in `workspace-library/index/influencer-os.sqlite` (`influencer_os/semantic_lookup.py`, stdlib-only, no provider calls), adopting the reference's portable design whole: heading-aware deterministic chunking with line provenance (chunker.ts), longest-prefix authority weights tunable per creator via `context/lookup-config.json` (discovery.ts), the relevance x authority x dampened-recency rerank with floor-ratio gate (reranker.ts; the FTS5 BM25 score mapped through a sigmoid stands in for non-negative cosine similarity), normalized-sha256 source change detection, a hard creator-scope leak boundary with dedicated no-leak tests (scope.ts; symlinked lookup sources fail closed and BM25 scoring is creator-local), and no query persistence (queries run on a read-only connection). The vector leg follows the reference exactly (local BGE-M3-class embedder, hash-embedder test double, RRF fusion over this same projection contract) when Command Centre is un-deferred — only the candidate generator changes; the chunk contract and rerank stages are already the reference's. This is a phasing of the reference's own hybrid design, not a divergence in kind (Decision 1, approved 2026-07-05). | Adopted (2026-07-06); Phase 2 slice 6; implements ADR 0011 |
| Research queries extract the core subject and avoid stale-knowledge contamination. | Each `ResearchSearchPlan` query carries a required `term_basis` enum array (`creator_profile`, `content_schedule`, `rolling_findings`, `research_intelligence`, `prior_queue`, `hypothesis`) so query-term provenance is auditable at rest and hypothesis terms are explicit; adapts `str-trending-research`'s `research-methodology.md` core-subject extraction into a schema field rather than prose. | Adopted (2026-07-04); extends ADR 0021 |

## Accepted Divergences

### Creator Personal Brand Board Projection

Agentic OS uses file-first brand context/style guides and explicit design-system
tokens. InfluencerOS adapts that pattern into a creator-scoped JSON contract plus
a rebuildable editable HTML projection because visual creator readiness requires
machine-checkable palette, typography, imagery, and layout rules. One shared
package template renders every creator; creator workspaces store only their spec
and projection. The user approved this adaptation on 2026-07-09 after the Mara
Vale run exposed that an approved abstract image was not a production brand
system.

| Divergence | Agentic OS reference | InfluencerOS decision | Reason | Status |
| --- | --- | --- | --- | --- |
| Local-first only in the first pass. | Agentic OS aims for access from anywhere through hosted or channel-based execution. | InfluencerOS v1 only needs to run well locally. | The user explicitly deprioritized multi-location access for now. | Accepted for v1 |
| Product-specific schemas are first-class contracts. | Agentic OS is mostly repo, standards, workflow, inventory, and skill context. | InfluencerOS uses JSON schemas as hard boundaries between workflow steps. | The product needs deterministic inputs and outputs for content generation planning. | Accepted |
| Creator Workspaces replace generic clients. | Agentic OS uses client folders for separation. | InfluencerOS uses creator-scoped workspaces under `workspace-library/creators/`. | The domain unit is a creator, not a client. | Accepted |
| No memory palace term in v1. | Agentic OS uses layered memory and semantic recall, not a memory palace term. | InfluencerOS uses SQL index, semantic lookup projection, and Creator Memory. | Prevents vague memory language and keeps recall tied to files, SQL, and provenance. | Accepted |
| Skill source and runtime copy split. | Agentic OS stores baseline runtime skills under `.claude/skills/` and syncs copied client skill folders. | InfluencerOS keeps baseline source skills under repo `skills/`, copies them into each Creator Workspace under `.claude/skills/`, and preserves creator `SKILL.local.md` on sync. | Keeps the public repo source layout simple while preserving client-root execution. | Accepted in ADR 0015 |
| No Agentic OS category prefixes. | Agentic OS names skills `{category}-{skill}` under `.claude/skills/{category}-{skill}/`. | InfluencerOS uses plain kebab-case skill names and groups by the skill-registry `category` column; no repo-root relocation. | Repo-central source is simpler for a single-product OS; the runtime copy already provides the `.claude/skills/` execution root. | Accepted in ADR 0017 |
| Creator Workspace propagation mechanism, gated content. | Agentic OS copies/syncs skills, scripts, settings, hooks, hook info, cron templates, instruction wrappers, learnings, and env into clients via `add-client.sh`/`update.sh`. | InfluencerOS builds the full propagation mechanism as Python CLI subcommands (`init-creator`, `sync-creator-runtime`, `update-creators`); it propagates skills and workspace structure now and carries inert zones for scripts/settings/hooks/cron until each subsystem is un-deferred. | Parity mechanism is approved; hooks/cron content is still deferred, so there is nothing to copy for those zones yet. | Accepted in ADR 0018 |
| Propagation via Python CLI, not bash scripts. | Agentic OS propagates via bash `scripts/` (`add-client.sh`, `update.sh`, `lib/pull.sh`). | InfluencerOS propagates via `influencer_os/` CLI subcommands. | The repo already standardized on a Python CLI surface. | Accepted in ADR 0018 |
| Key presence is standing approval for research-acquisition connectors. | Agentic OS activates `str-trending-research` (OpenAI Reddit, xAI X), Firecrawl, and Apify connectors on API-key presence with no exact-approval gate. | InfluencerOS builds the same research-acquisition connectors as an env-gated layer and adopts standing approval for that tier only (bounded by a per-run call cap and a kill switch); generation stays exact-approved except for ADR 0043's one bounded approved-plan creator-setup reference pass. | The manual research loop needs real Reddit/X source access with engagement metrics now; a per-run prompt was rejected as too much friction, and the weakening is bounded and tier-scoped. | Accepted in ADR 0022, amended for setup references by ADR 0043 |

## Open Alignment Decisions

Open alignment decisions are tracked here. When one is resolved, move it to Accepted Divergences with an ADR reference.

No open alignment decisions at this time. The propagation-mechanism decision was resolved in ADR 0018: the mechanism is approved and built as CLI subcommands, while the scripts, settings, hooks, and cron content zones stay inert until each subsystem is un-deferred by its own approval (tracked in the roadmap Deferred sections).

## Decision Rule

If a difference is not listed above or recorded in `docs/adr/`, treat it as unapproved.

Before coding an unapproved divergence, run `docs/os-construction/divergence-test.md`, create or update an ADR or this alignment doc, and ask the user to confirm the decision.
