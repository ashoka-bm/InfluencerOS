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

Upstream input: the locked IdeaPromotion, named by the seed's
`idea_promotion_id` (or owned by the bundle in section 2). Standalone
scaffolding takes the promotion's single unclaimed pre-listed project id
(pin `project_id` in the seed when several are unclaimed); a project the
promotion never listed needs a new promotion package, not a scaffold.

| Field | Class | Rule |
| --- | --- | --- |
| `idea_promotion_id` | authored | Names the upstream promotion (the one seed field that is also copied into `source_refs`) |
| `project_slug` | authored | |
| `content_unit_type` | authored | Must map to a production-supported format |
| `platform_targets` | authored | Surface-level targets (e.g. `youtube_shorts`); advisory platform-fit warning unchanged |
| `learning_goal` | authored | Derived from intended payoff and measurement expectation |
| `acceptance_criteria` | authored | |
| `constraints`, `dependencies`, `notes` | authored | Optional |
| `source_refs.reference_asset_ids` | authored | Asset selection is a judgment call |
| `project_id` | derived | `project_<creator>_<slug-ish>_<seq>`; seed may pin |
| `creator_profile_id` | derived | From the workspace profile |
| `created_on` | derived | Today |
| `status` | derived | `created` |
| `target_formats` | derived | Default `[format_<content_unit_type>]`; seed may override with a subset of the promotion's `approved_formats` |
| `project_paths` | derived | Constant block, identical for every project |
| `source_refs.idea_promotion_id` | copied | The single upstream ref, from the seed's named promotion |
| `source_refs.{idea_queue_entry_id, research_finding_ids, research_evidence_ids, metric_snapshot_ids, video_understanding_pack_ids}` | copied | Cached refs, lifted from the locked promotion (subsets by construction; empty ones omitted) |
| `source_refs.evidence_brief_path` | derived | `evidence-brief.md` |

The constructor subsumes today's `init-project` (directory scaffold,
evidence-brief skeleton, platform-fit advisory) — one invocation, not
author-then-copy.

Canonical seed:

```json
{
  "idea_promotion_id": "idea_promotion_luna_fit_001",
  "project_slug": "tiny-reset-after-laptop-day",
  "content_unit_type": "short_form_video",
  "platform_targets": ["youtube_shorts", "instagram_reels", "tiktok"],
  "reference_asset_ids": ["asset_luna_identity_plate"],
  "learning_goal": "Test whether a visible workday constraint plus a tiny relief routine improves early retention.",
  "acceptance_criteria": [
    "A validated micro-journey production plan exists for the short-form video format."
  ],
  "constraints": ["No provider-backed generation calls without explicit user approval."],
  "notes": "Created from the locked lunch-break reset promotion."
}
```

## 2. IdeaPromotion Bundle (`stage promotion` / `commit-stage`)

Upstream input: the promoted IdeaQueueEntry (`--entry <id>`), the content
schedule, and the queue manifest. The bundle stages the promotion, one
project per embedded project seed, evidence-brief skeletons, and the
planned entry/slot/queue flips.

| Field | Class | Rule |
| --- | --- | --- |
| `approved_platforms` | authored | Subset choice presented at the gate |
| `approved_formats` | authored | Subset choice; at least one production-supported |
| `schedule_slot_ids` | authored | Slot claims (omitted for wildcards); slot-gate rules unchanged |
| `creative_elements_to_carry_forward` | authored | Curated from the entry's creative notes |
| `approval_note` | authored | Only when the user volunteers one |
| `projects` | authored | Embedded project seeds (section 1) |
| `idea_promotion_id` | derived | Pattern + sequence |
| `creator_profile_id` | derived | From the workspace |
| `promotion_status` | derived | `active` |
| `project_ids_created` | derived | From the embedded project seeds (ids allocated at stage time, so the promotion lists them up front as `init-project` requires) |
| `idea_queue_entry_id` | copied | The `--entry` argument |
| `intended_payoff`, `intended_emotion`, `core_message` | copied | Verbatim from the entry (ADR 0024); an entry missing the intent pair blocks staging — fix the entry first |
| `research_finding_ids` | copied | From the entry's `source_finding_ids` |
| `evidence_refs` | copied | Entry's structured refs, verbatim shape |
| `score_snapshot` | copied | Entry's eight scores + rationales, verbatim |
| `approved_by` | stamped | `user`, at commit |
| `approved_on` | stamped | Commit date (stage uses the staging date provisionally so drafts validate) |

Commit-side flips (previously hand-sequenced by the skill, now owned by
`commit-stage`, in construction order): write promotion → write projects →
evidence briefs → entry flip (`status: promoted`, append
`linked_idea_promotion_ids` / `linked_project_ids`, `updated_on`) → queue
manifest `status_counts` → claimed slots to `filled` → validate → rebuild
board and index.

Stage hashes cover: the entry file, the claimed slots' `research_state`,
and the queue manifest row. Any change between stage and commit fails the
commit closed.

Present-from-draft: the skill presents the approval package from the staged
records, so the human approves exactly the bytes that commit will write.
Supersession and cancellation lifecycles are unchanged (new stage → new
promotion; the old one flips to `superseded`).

Canonical seed:

```json
{
  "approved_platforms": ["instagram", "tiktok", "youtube"],
  "approved_formats": ["format_short_form_video"],
  "schedule_slot_ids": ["slot_2026_07_14_reel"],
  "creative_elements_to_carry_forward": [
    "Hook: open on the slumped-at-desk exhale before any speech."
  ],
  "projects": [
    {
      "project_slug": "tiny-reset-after-laptop-day",
      "content_unit_type": "short_form_video",
      "platform_targets": ["youtube_shorts", "instagram_reels", "tiktok"],
      "learning_goal": "Test whether a visible workday constraint plus a tiny relief routine improves early retention.",
      "acceptance_criteria": [
        "A validated micro-journey production plan exists for the short-form video format."
      ]
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
| `outputs.idea_queue_entry_ids` | derived | Queue entries whose `evidence_refs` cite the run |
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

## Anticipation Points

| Trigger | Deterministic work started |
| --- | --- |
| Creator session opens | `refresh-workspace <ws>` (background): validate all + index/lookup/board rebuilds |
| Search plan written | `research-fetch --plan <plan> --run-dir <staged-run-dir>` (background): every connector-routable planned fetch runs concurrently; jobs derive only from adapters the plan marked `use_now` |
| Promotion package about to be presented | `stage promotion` — draft bundle built while the human reads |
| Any constructor write | Post-write validate + projection rebuilds, same invocation |

Never anticipated: provider-backed generation, publishing, scheduling,
unattended runs. Never written pre-gate: any canonical record behind a
human approval.
