# Record Constructors And Seed Contracts

Decision record: `docs/adr/0042-seed-based-record-constructors.md`.

For record types listed here, skills author a **seed** — only the genuinely
authored fields — and a deterministic constructor assembles the full
canonical record. Skills never hand-author a full record for a type that
has a constructor; `python3 -m influencer_os scaffold --list` enumerates
them.

## Field Classes

Every field of a constructed record belongs to exactly one class:

| Class | Who supplies it | Examples |
| --- | --- | --- |
| **authored** | The seed (model/human judgment) | learning goals, acceptance criteria, planned queries |
| **derived** | Constructor computes deterministically | ids, dates, initial statuses, constant path blocks |
| **copied** | Constructor reads from the upstream record on disk | score snapshots, evidence refs, intent pair |
| **stamped** | Constructor fills at gate/commit time | `approved_on`, `approved_by` |

Rules every constructor follows:

- Validate the assembled record against its schema before writing; write
  atomically (`write_json_atomic`).
- Run the type's standard post-write pipeline (targeted `validate`,
  projection rebuilds) in the same invocation.
- Allocate ids from the type's pattern plus the next free sequence in the
  workspace; a seed may pin an id explicitly.
- Reject a seed that supplies a derived or copied field with a conflicting
  value (fail closed, never silently overwrite).
- Carry a fixture test: the canonical seed in this document must scaffold
  to a schema-valid record. A schema change that breaks construction is a
  test failure.

Staged bundles live under `<ws>/system/staging/<stage-id>/` with content
hashes of their upstream inputs. `commit-stage` re-verifies hashes, stamps
approval fields, writes in construction order, and runs the post-write
pipeline. A stale stage fails closed and is re-staged, never patched.

---

## 1. Project Manifest (`scaffold project`)

Upstream input: the locked ConceptApproval, named by the seed's
`concept_approval_id` (or owned by the bundle in section 2). Standalone
scaffolding takes the approval's single unclaimed pre-listed project id
(pin `project_id` in the seed when several are unclaimed); a project the
approval never listed needs a new approval package, not a scaffold.

| Field | Class | Rule |
| --- | --- | --- |
| `concept_approval_id` | authored | Names the upstream approval (the one seed field that is also copied into `source_refs`) |
| `project_slug` | authored | |
| `content_unit_type` | authored | Must map to a production-supported format |
| `platform_targets` | authored | Surface-level targets (e.g. `youtube_shorts`); advisory platform-fit warning unchanged |
| `learning_goal` | authored | Derived from intended payoff and measurement expectation |
| `acceptance_criteria` | authored | |
| `commercial_expression` | authored | One Concept-approved commercial function plus exact offer integration and CTA intensity at or below the approval ceilings (ADR 0030) |
| `constraints`, `dependencies`, `notes` | authored | Optional |
| `source_refs.reference_asset_ids` | authored | Asset selection is a judgment call |
| `project_id` | derived | `project_<creator>_<slug-ish>_<seq>`; seed may pin |
| `creator_profile_id` | derived | From the workspace profile |
| `created_on` | derived | Today |
| `status` | derived | `created` |
| `target_formats` | derived | Default `[format_<content_unit_type>]`; seed may override with a subset of the approval's `approved_formats` |
| `project_paths` | derived | Constant block, identical for every project |
| `source_refs.concept_approval_id` | copied | The single upstream ref, from the seed's named approval |
| `source_refs.{campaign_concept_id, campaign_id}` | copied | Cached chain ids; must match the transitive approval chain |
| `source_refs.{research_finding_ids, research_evidence_ids, metric_snapshot_ids, video_understanding_pack_ids}` | copied | Cached refs, lifted from the locked approval and its concept (subsets by construction; empty ones omitted) |
| `source_refs.evidence_brief_path` | derived | `evidence-brief.md` |

The constructor subsumes today's `init-project` (directory scaffold,
evidence-brief skeleton, platform-fit advisory) — one invocation, not
author-then-copy.

Canonical seed:

```json
{
  "concept_approval_id": "concept_approval_luna_fit_001",
  "project_slug": "tiny-reset-after-laptop-day",
  "content_unit_type": "short_form_video",
  "platform_targets": ["youtube_shorts", "instagram_reels", "tiktok"],
  "reference_asset_ids": ["asset_luna_identity_plate"],
  "learning_goal": "Test whether a visible workday constraint plus a tiny relief routine improves early retention.",
  "acceptance_criteria": [
    "A validated micro-journey production plan exists for the short-form video format."
  ],
  "constraints": ["No provider-backed generation calls without explicit user approval."],
  "commercial_expression": {
    "commercial_function": "lead_capture",
    "offer_integration": "embedded",
    "cta_intensity": "soft"
  },
  "notes": "Created from the locked lunch-break reset approval."
}
```

## 2. ConceptApproval Bundle (`stage approval` / `commit-stage`)

Upstream input: the Campaign Concept being approved (`--concept <id>`,
status `ready_for_approval` or `active`) and the content schedule. The
bundle stages the approval, one project per embedded project seed,
evidence-brief skeletons, and the planned concept/slot flips. One
unchanged concept may receive later approvals for additional projects;
earlier approvals stay active as the provenance lock for their projects.

| Field | Class | Rule |
| --- | --- | --- |
| `approved_platforms` | authored | Subset choice presented at the gate |
| `approved_formats` | authored | Subset choice; at least one production-supported |
| `max_offer_integration`, `max_cta_intensity` | authored | Commercial-expression ceilings (ADR 0030) |
| `approval_note` | authored | Only when the user volunteers one |
| `projects` | authored | Embedded project seeds (section 1, plus per-project `commercial_expression`, optional `schedule_slot_ids` — each slot hosts one project — and `evidence_brief`) |
| `concept_approval_id` | derived | Pattern + sequence |
| `creator_profile_id` | derived | From the workspace |
| `approval_status` | derived | `active` |
| `schedule_slot_ids` | derived | Union of the per-project slot claims |
| `project_ids_created` | derived | From the embedded project seeds (ids allocated at stage time, so the approval lists its exact project set up front) |
| `campaign_concept_id` | copied | The `--concept` argument |
| `intended_payoff`, `intended_emotion`, `core_message` | copied | Verbatim from the concept (ADR 0024); a concept missing the intent pair blocks staging — fix the concept first |
| `evidence_refs` | copied | Concept's structured refs, verbatim shape (the gate re-verifies the copy stayed verbatim) |
| `approved_by` | stamped | `user`, at commit |
| `approved_on` | stamped | Commit date (stage uses the staging date provisionally so drafts validate) |

Commit-side flips (owned by `commit-stage`, in construction order): write
approval → write projects → evidence briefs → concept flip
(`status: active`, `updated_on`) → claimed slots to `filled` with their
ownership refs (`campaign_id`, `campaign_concept_id`, `project_id`) →
validate → rebuild board and index.

Stage hashes cover: the concept file and the claimed slots'
`research_state`. Any change between stage and commit fails the commit
closed.

Present-from-draft: the skill presents the approval package from the staged
records, so the human approves exactly the bytes that commit will write.
Supersession and cancellation lifecycles follow `approve-concept` (new
stage → new approval; a replaced one flips to `superseded`).

Canonical seed:

```json
{
  "approved_platforms": ["instagram", "tiktok", "youtube"],
  "approved_formats": ["format_short_form_video"],
  "max_offer_integration": "embedded",
  "max_cta_intensity": "soft",
  "projects": [
    {
      "project_slug": "tiny-reset-after-laptop-day",
      "content_unit_type": "short_form_video",
      "platform_targets": ["youtube_shorts", "instagram_reels", "tiktok"],
      "learning_goal": "Test whether a visible workday constraint plus a tiny relief routine improves early retention.",
      "acceptance_criteria": [
        "A validated micro-journey production plan exists for the short-form video format."
      ],
      "commercial_expression": {
        "commercial_function": "lead_capture",
        "offer_integration": "embedded",
        "cta_intensity": "soft"
      },
      "schedule_slot_ids": ["slot_luna_2026_07_09_midweek"]
    }
  ]
}
```

## 3. ResearchSearchPlan + ResearchRun Pair

Two moments, one shared header. The plan is authored at planning time; the
run record is written at completion (its `run_status` enum has only
terminal values) and derives every shared field from the plan — the drift
class `migrate_slot_research` exists to reconcile can no longer occur.

In-flight runs are themselves staged state: `scaffold search-plan` creates
`system/staging/research-runs/<research_run_id>/` holding the plan, the
connector budget, and the accumulating `fetch-results/`, `evidence.jsonl`,
`metric-snapshots.jsonl`, and `source-yield.jsonl` ledgers. `complete-run`
derives and validates the run record, then moves the whole folder into
canonical `research/runs/` — at-rest validation's invariant (every
canonical run folder is complete and valid) never sees a half-finished
run. A completed (non-failed) run must carry its `source-yield.jsonl`
before it can complete.

### `scaffold search-plan`

| Field | Class | Rule |
| --- | --- | --- |
| `mode`, `scope` | authored | |
| `platforms` | authored | ADR 0020/0027 platform set |
| `schedule_slot_ids` | authored | Slot-first provenance (empty for broad runs) |
| `decision_basis` | authored | The planning judgment |
| `adapters_considered`, `planned_queries`, `planned_sources`, `skipped_sources`, `approval_gates`, `future_connector_notes` | authored | ADR 0021/0022 contracts unchanged |
| `research_search_plan_id`, `research_run_id` | derived | Run id allocated at plan time so both records share it |
| `creator_profile_id` | derived | From the workspace |
| `created_on` | derived | Today |

Writing the plan is the fan-out trigger: `research-fetch --plan
<search-plan>` runs all planned connector fetches concurrently in one
process (standing approval, call caps, and the kill switch per ADR 0022),
typically as a background task started as soon as the plan exists.

### `complete-run`

| Field | Class | Rule |
| --- | --- | --- |
| `material_update` | authored | `--material-update` / `--no-material-update` |
| `error` | authored | `--error`; marks the run failed |
| `outputs.finding_ids` | authored-with-scan-default | Explicit `--finding` ids, else stable findings citing the run (the rolling `findings.md` cites runs too coarsely to attribute) |
| `outputs.research_intelligence_updates` | authored | `--intelligence` notes |
| `research_run_id`, `creator_profile_id`, `mode`, `scope`, `schedule_slot_ids`, `platforms` | copied | Verbatim from the search plan |
| `started_on`, `completed_on` | derived | Plan creation time / now |
| `outputs.{evidence_ids, metric_snapshot_ids}` | derived | Scanned from the run's ledgers, so the outputs↔JSONL closure holds by construction |
| `outputs.content_opportunity_ids` | derived | Content opportunities whose `evidence_refs` cite the run |
| `run_status` | derived | From `material_update` and error state |

Canonical seed (plan):

```json
{
  "mode": "scheduled_needs",
  "scope": "Desk-reset relief content for the July 14 reel slot",
  "platforms": ["instagram", "tiktok", "youtube"],
  "schedule_slot_ids": ["slot_2026_07_14_reel"],
  "decision_basis": {"summary": "Slot is unresearched; prior desk-reset finding is 3 weeks old."},
  "adapters_considered": [],
  "planned_queries": [],
  "planned_sources": [],
  "skipped_sources": [],
  "approval_gates": [],
  "future_connector_notes": []
}
```

(`decision_basis` and the planning arrays keep their existing ADR 0021
shapes; the seed above elides their bodies, and the fixture test uses a
fully populated variant.)

---

## 4. Campaign (`scaffold_campaign` / `activate_campaign`)

Upstream input: the creator profile (pillars) and `conversion-assets/`
(paid offer, when named). New campaigns are born `draft`;
`activate_campaign` records the human activation decision (approval
metadata, not a new production Gate — ADR 0029).

| Field | Class | Rule |
| --- | --- | --- |
| `name`, `objective`, `measurable_outcome` | authored | Objective from the ADR 0029 vocabulary |
| `primary_content_pillar_id`, `supporting_content_pillar_ids` | authored | Must resolve to creator-profile pillars |
| `primary_audience_segment`, `supporting_audience_segments` | authored | Audience is a creator-profile input; free-form, never invented |
| `primary_offer_conversion_asset_id`, `supporting_conversion_asset_ids` | authored | Offer required when objective is `paid_conversion`; must resolve under `conversion-assets/` |
| `notes` | authored | Optional |
| `campaign_id` | derived | `campaign_<creator>_<seq>`; seed may pin |
| `creator_profile_id`, `created_on`, `updated_on` | derived | |
| `status` | derived | `draft` |
| `activation` | stamped | `approved_by: user` + `activated_on` at activation |

Canonical seed:

```json
{
  "name": "Desk-reset habit builder",
  "objective": "lead_generation",
  "primary_content_pillar_id": "pillar_tiny_home_workouts",
  "supporting_content_pillar_ids": ["pillar_no_shame_fitness"],
  "primary_audience_segment": "Time-constrained women who want low-pressure home movement.",
  "supporting_audience_segments": ["Beginners returning to movement after a long break"],
  "primary_offer_conversion_asset_id": "conversion_asset_luna_reset_checklist",
  "supporting_conversion_asset_ids": [],
  "measurable_outcome": "Grow reset-checklist downloads from desk-reset content to 200 per month.",
  "notes": "Runs indefinitely; a paid-offer change would open a new campaign."
}
```

## 5. CampaignConcept (`scaffold_campaign_concept`)

Upstream input: the owning Campaign, and the assigned Content Opportunity
when one exists. A concept only selects Campaign-approved audience
segments and pillars; evidence is copied from the assigned opportunity
(authored directly only for campaign-scoped research with no opportunity).

| Field | Class | Rule |
| --- | --- | --- |
| `campaign_id` | authored | The owning campaign |
| `title`, `hypothesis`, `audience_tension`, `promise` | authored | The testable hypothesis; a material change creates a new linked concept |
| `audience_segment`, `content_pillar_id` | authored | Must be Campaign-approved |
| `primary_commercial_function`, `supporting_commercial_functions` | authored | ADR 0030 vocabulary |
| `source_content_opportunity_id` | authored | The assignment judgment, when assigning from the queue |
| `evidence_refs` | copied / authored | Copied from the assigned opportunity; authored only without one |
| `related_concepts`, `notes` | authored | Optional |
| `campaign_concept_id` | derived | `campaign_concept_<creator>_<seq>`; seed may pin |
| `creator_profile_id`, `created_on`, `updated_on` | derived | |
| `status` | derived | `draft` |

Canonical seed:

```json
{
  "campaign_id": "campaign_luna_fit_001",
  "title": "Lunch-break resets beat willpower plans",
  "hypothesis": "Desk workers act on a reset they can finish inside a lunch break, not on plans that ask for a schedule change.",
  "audience_tension": "By midday the body feels wrecked, but every fitness plan seems to demand an hour that does not exist.",
  "promise": "A ninety-second reset you can run beside the desk today, no outfit change, no equipment.",
  "audience_segment": "Time-constrained women who want low-pressure home movement.",
  "content_pillar_id": "pillar_tiny_home_workouts",
  "primary_commercial_function": "lead_capture",
  "supporting_commercial_functions": ["trust_building"],
  "source_content_opportunity_id": "content_opportunity_luna_fit_001",
  "related_concepts": [],
  "notes": "Assigned from the lunch-break reset opportunity; hooks and formats vary per project."
}
```

## 6. ContentOpportunity (`scaffold_content_opportunity`)

Wildcard research output without a Campaign owner (ADR 0031). The
constructor writes the entry and upserts the queue manifest in the same
invocation, so entry and manifest never drift. Assignment (flipping to
`assigned` and linking the created concept) is part of the Slice 3
workflow cutover.

| Field | Class | Rule |
| --- | --- | --- |
| `title`, `hook`, `premise_summary`, `intended_payoff`, `topic_cluster` | authored | |
| `platform_recommendations`, `format_recommendations`, `schedule_fit_type` | authored | Canonical enums |
| `evidence_refs`, `scores` | authored | Research provenance and the eight scored dimensions |
| intent pair + notes fields (`intended_emotion`, `core_message`, `urgency_window`, ...) | authored | Optional |
| `content_opportunity_id` | derived | `content_opportunity_<creator>_<seq>`; seed may pin |
| `creator_profile_id`, `created_on`, `updated_on` | derived | |
| `status` | derived | `new` |
| queue manifest (`entry_refs`, `status_counts`, `updated_on`) | derived | Upserted with the entry |
| `linked_campaign_concept_ids` | stamped | At assignment (Slice 3) |

The canonical seed is the example entry minus constructor-owned fields
(`examples/content-opportunity.example.json`); the fixture test derives it
mechanically.

ConceptApproval intentionally has no standalone scaffold: an approval and
its exact Project set are one transactional operation behind the human
gate (ADR 0029), so its constructor is the staged approval bundle that
replaces `stage promotion`/`commit-stage` at the workflow cutover.

## Anticipation Points

| Trigger | Deterministic work started |
| --- | --- |
| Creator session opens | `refresh-workspace <ws>` (background): validate all + index/lookup/board rebuilds |
| Search plan written | `research-fetch --plan <plan> --run-dir <staged-run-dir>` (background): every connector-routable planned fetch runs concurrently; jobs derive only from adapters the plan marked `use_now` |
| Approval package about to be presented | `stage approval` — draft bundle built while the human reads |
| Any constructor write | Post-write validate + projection rebuilds, same invocation |

Never anticipated: provider-backed generation, publishing, scheduling,
unattended runs. Never written pre-gate: any canonical record behind a
human approval.
