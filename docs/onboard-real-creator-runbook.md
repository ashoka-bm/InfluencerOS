# Onboard A Real Creator — Day-1 Runbook

Last updated: 2026-07-07

This is the operator runbook for the first contact between InfluencerOS and
real creator data (roadmap Post-Phase-4 Track 1). Everything before this
point produced disposable fixtures; this document is what changes when the
subject is real. Follow it top to bottom the first time.

## 1. Understand What Changes

Until now, every workspace under `workspace-library/creators/` was a
disposable build/test fixture. A real creator workspace is different in three
ways:

- **It is not recoverable from git.** `workspace-library/` is gitignored by
  design (private creator data never enters the repo), so a deleted real
  workspace is gone. Back it up (step 3).
- **It must not share the directory with stale fixtures.** Wipe the fixtures
  first (step 2) so no future cleanup can confuse real data with test data.
- **The release gate applies.** A real workspace's health claim is
  `validate all`, not any single scoped validator.

## 2. One-Time: Wipe The Disposable Fixtures

Do this once, immediately before onboarding the first real creator. This is
**irreversible** — the fixtures are not in git. They are rebuildable from
`examples/` if ever needed again.

List what exists, delete each fixture by name (never `rm -rf` the whole
`creators/` directory once any real creator lives there), and remove the
rebuildable index:

```bash
ls workspace-library/creators/
rm -rf workspace-library/creators/<fixture-slug>   # repeat per fixture
rm -rf workspace-library/index/
```

Verify the directory is empty before proceeding: `ls workspace-library/creators/`.

## 3. One-Time: Decide The Backup Discipline

Real creator workspaces live only on this disk. Before onboarding, ensure at
least one of:

- the machine's system backup (Time Machine or equivalent) covers the repo
  path including `workspace-library/`, or
- a periodic `rsync` of `workspace-library/` to a second disk or private
  location the operator controls.

Never push `workspace-library/` contents to the repo; the `.gitignore` entry
is a privacy boundary, not an accident.

## 4. Prerequisites: Environment And Connectors

Copy `.env.example` to `.env` (gitignored) and fill in the research keys you
have. Key presence is standing approval for that connector's
research-acquisition calls (ADR 0022); the guardrails are the per-run call
cap (`INFLUENCER_OS_CONNECTOR_MAX_CALLS`, default 12) and the kill switch
(`INFLUENCER_OS_DISABLE_PAID_CONNECTORS=1`).

Confirm which connectors are live:

```bash
python3 -m influencer_os list-connectors
```

Before trusting a connector for real research, run one bounded smoke fetch
and read the parsed output (the parsers were built against mirrored response
shapes; ADR 0022 "run 2" validates them live):

```bash
INFLUENCER_OS_CONNECTOR_MAX_CALLS=3 python3 -m influencer_os research-fetch reddit "<topic>" --days 30
```

Generation providers are separate and stricter: key presence is **never**
approval, every provider call needs an exact human-approved
`GenerationApprovalRecord`, and only the deterministic `mock` adapter is
installed until a real provider adapter is approved as its own batch
(ADR 0023 Decision 3).

## 5. Onboard The Creator

Run the `create-influencer` conductor skill (`skills/create-influencer/`).
It offers three intake paths — load existing files, guided interview, or
generate from basic information — and drives the full foundation: identity,
soul, personal brand, voice samples, creator profile, runtime context, and
reference library.

The CLI seams it uses, in order:

```bash
python3 -m influencer_os init-creator <workspace-manifest>
python3 -m influencer_os import-intake <source-file> --creator-workspace <workspace> --source-type <type> --notes "<note>"
python3 -m influencer_os set-intake-status <workspace> <source-id> drafted   # then: reviewed
python3 -m influencer_os validate workspace <workspace>
```

Readiness is status-keyed: the workspace stays permissive at `draft` and must
pass the medium-based blockers to claim `content_ready`, `generation_ready`,
or `active`. Do not hand-set a status the validator has not confirmed.

## 6. Research → Ideas → Promotion → Production

The producer skills own each phase; the `influencer-os` conductor routes
between them and halts at every human gate.

- Research runs and findings: `create-research-findings` (research runs are
  dated, sourced, platform-scoped; connectors feed evidence when keyed).
- Idea queue: `manage-idea-queue` (scored, evidence-linked entries; never
  promotes).
- Promotion: `promote-idea` — **the human approval gate**. Nothing enters
  production without an explicit user-approved promotion package.
- Production planning: `apply-social-template` and `create-production-plan`.
- Packaging: `register-output-package`.

Keep the projections fresh as records change:

```bash
python3 -m influencer_os rebuild-board <workspace>
python3 -m influencer_os rebuild-index <workspace>
python3 -m influencer_os rebuild-lookup <workspace>
```

## 7. The Release Gate

At any milestone — end of onboarding, after a research cycle, before and
after promotion, after packaging — the health claim for the workspace is the
composed run:

```bash
python3 -m influencer_os validate all <workspace>
```

It chains workspace, research, queue, board, and every project, names the
failing layer, and counts warnings in its summary line. Read the warnings:
human-approved promotions with unresolved evidence refs warn rather than
fail by design, and a warning you cannot explain is a finding.

## 8. What Never Happens In V1

- No publishing, scheduling, or platform posting — output packages are
  registered, publication is recorded manually after the fact
  (`register-published-post`).
- No automated idea promotion and no provider call without an exact approval.
- No scheduled/unattended research (deferred; ADR 0025).
- No creator media, generated works, or `.env` contents committed to git.
