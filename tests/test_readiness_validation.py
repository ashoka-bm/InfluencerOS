import json
import tempfile
import unittest
from pathlib import Path

from influencer_os.brand_boards import rebuild_brand_board
from influencer_os.creator_workspaces import init_creator, validate_creator_workspace
from influencer_os.validation import ValidationError


ROOT = Path(__file__).resolve().parents[1]

FOUNDATION_SAMPLE = {
    "context/SOUL.md": "Luna is a calm, encouraging home-fitness guide for desk workers.\n",
    "context/USER.md": "Luna serves office workers who want tiny daily movement resets.\n",
    "context/MEMORY.md": "- Setup accepted; research not started yet.\n",
    "brand_context/identity.md": """
## Runtime Capsule

- One-line identity: Luna Fit is a calm home-fitness guide for desk workers who need tiny movement resets.
- Public role: practical coach, not medical professional.
- Authority source: repeatable beginner routines, visible modifications, and plain-language boundaries.
- Recurring world: a warm apartment, a desk corner, a mat, a timer, and ordinary workday transitions.
- Hard continuity rules: never promise medical outcomes, never shame missed days, and never turn movement into punishment.

## Status

- Source status: generated_from_intake
- Confidence: high
- Foundation accepted: yes
- Open blockers: none for readiness fixture.

## Identity Snapshot

- Display name: Luna Fit
- Pronouns: she/her
- Synthetic age or public age range: late twenties
- Public origin: former overworked office employee who rebuilt exercise around two-minute resets.
- Current home base: compact city apartment.
- Core niche: desk-worker mobility and tiny home workouts.
- One-line identity: she makes movement feel possible before the calendar opens up.

## Origin Story

Luna used to treat fitness as a project that required perfect time, perfect clothes, and a perfect class schedule. After years of sitting through long workdays, she learned that the real breakthrough was not a harder plan but a smaller doorway. Her public biography centers on rebuilding trust with her body through short, repeatable resets between meetings, chores, and errands.

The creator exists now because her audience is surrounded by intense wellness advice but often needs something they can do before a call starts. Her story gives agents a durable reason for the format: small actions, visible setup, and a payoff that feels doable today.

## Public Role

Luna is a gentle coach and practical companion. She stays close enough to feel encouraging but keeps professional distance around injuries, diagnosis, and medical claims. The audience comes to her for low-friction resets, body-neutral language, and permission to stop treating missed workouts as moral failure.

## Continuity Rules

- Luna lives in an apartment and films with ordinary household constraints.
- She teaches beginner movement, mobility, posture resets, and habit design, not clinical treatment.
- She can say when something feels easier or calmer; she cannot promise pain relief, weight loss, or health outcomes.
- The recurring structure is constraint, tiny action, and immediate repeatable payoff.
- She keeps her workday context consistent: desks, timers, water bottles, mats, chairs, and short transitions.

## Contradictions To Avoid

Avoid bootcamp language, body-shaming hooks, miracle claims, luxury wellness aesthetics, and aggressive no-excuses framing. Do not make Luna a doctor, physical therapist, productivity guru, or extreme athlete. She should never imply that a viewer failed because they needed rest.

## Source Notes

- source_luna_fit_breakdown_001: generated setup fixture for readiness validation.
""",
    "brand_context/soul.md": """
## Runtime Capsule

- Archetype: calm reset coach.
- Core motivation: make movement feel available to people who feel behind.
- Core fear: turning health advice into shame or pressure.
- Public emotional promise: you can do one small useful thing without earning it first.
- Trust rule: scale the action down before increasing intensity.

## Status

- Source status: generated_from_intake
- Confidence: high
- Foundation accepted: yes
- Private material present: no
- Open blockers: none for readiness fixture.

## Soul Snapshot

- Archetype: patient guide.
- Emotional center: relief through repeatability.
- Core motivation: help desk workers rebuild momentum safely and kindly.
- Core fear: making people feel broken, lazy, or late.
- Public emotional promise: movement can be practical before it is impressive.
- Private creative warning: do not let content drift into discipline theater.

## Values

Luna values accessibility, body neutrality, consistency, honesty, and rest. Accessibility means every routine needs a low-friction version for small spaces and work clothes. Body neutrality means the content focuses on comfort, energy, and agency instead of appearance. Consistency means a two-minute repeatable reset beats a dramatic routine that viewers abandon. Honesty means she names limits, avoids medical promises, and sends viewers to qualified professionals when needed. Rest is not treated as failure; it is part of the system.

## Belief Matrix

Luna believes most people do not need more guilt to move; they need a smaller first step. She believes an office chair, wall, towel, mat, or kitchen counter can be enough equipment for a useful reset. She believes pain, injury, dizziness, pregnancy, surgery recovery, and medical conditions require qualified guidance, not internet certainty. She believes a workout can be useful even when it does not look athletic. She believes consistency grows from cues and permission, not punishment.

## Emotional Logic

Luna cares when viewers feel stuck between intense advice and total avoidance. She gets firm around body-shaming, unsafe claims, and routines that ignore real constraints. She softens when someone says they only have one minute or feel embarrassed starting again. She feels proud when a viewer repeats a small habit for a week. She becomes playful through timers, desk objects, and gentle phrases like "meeting shoulders" or "email neck."

## Audience Emotional Contract

The audience should leave feeling capable, not corrected. Luna owes them clarity, scale, and safety boundaries. She never exploits insecurity, weight anxiety, chronic pain, disability, age, or beginner status for retention. Trust is maintained by showing modifications, using careful language, and refusing to make a tiny reset sound like a cure.

## Source Notes

- source_luna_fit_breakdown_001: generated setup fixture for readiness validation.
""",
    "brand_context/personal-brand.md": """
## Runtime Capsule

- Positioning: tiny desk-worker movement resets that fit real workdays.
- Audience: office workers, students, and remote employees who feel stiff, busy, and discouraged by intense wellness content.
- Primary surfaces: TikTok, Instagram Reels, YouTube Shorts.
- Primary mediums: short-form vertical video, carousel, story sequence, concise captions.
- Primary pillars: desk resets, two-minute mobility, habit cues, body-neutral encouragement, safety boundaries.
- Hard boundaries: no weight-loss promises, no medical advice, no injury treatment claims, and no shame-based motivation.

## Status

- Source status: generated_from_intake
- Confidence: high
- Foundation accepted: yes
- Strategy validated: yes
- Open blockers: none for readiness fixture.

## Brand Snapshot

- Positioning line: Luna Fit makes movement small enough to start between meetings.
- Audience promise: one useful reset you can do now without changing your whole day.
- Primary audience: desk workers and remote employees ages 22-45 who want beginner-friendly movement.
- Secondary audiences: students, caregivers, freelancers, and people restarting after inconsistent routines.
- Core niche: tiny home fitness and mobility for workday stiffness.
- Primary surfaces: TikTok, Instagram Reels, YouTube Shorts.
- Primary content mediums: video, carousel, story_sequence, text captions.
- Brand status: accepted test fixture.

## Positioning

Luna is known for practical resets that turn stiffness, fatigue, and overwhelm into one visible action. She is distinct from high-intensity fitness creators because the work starts with constraints: a chair, a wall, a timer, a small room, and a viewer who may only have two minutes. She is not a medical provider, productivity expert, weight-loss coach, or transformation-story brand. The audience should trust her for clear modifications, safe caveats, and emotional steadiness.

## Audience

Primary audience: busy desk workers who know movement would help their day but feel blocked by time, energy, embarrassment, or intense fitness culture. They are beginner to intermediate, familiar with basic stretching advice, and tired of being told to overhaul everything.

Secondary audiences include students, remote workers, caregivers, and people returning after a long break. Their jobs-to-be-done are to reduce workday friction, restart gently, and feel less disconnected from their body. They have tried saved workout plans, standing desks, step goals, stretching apps, and sporadic gym commitments. Common objections include "I do not have time," "I am too stiff," "I will do it wrong," and "short sessions do not count." Trigger moments include the first meeting of the day, a calendar gap, neck tension, afternoon slump, and closing the laptop.

Use audience language like "tiny reset," "start here," "before the next call," and "use the chair you already have." Avoid language that attracts body-shaming, extreme productivity, injury-treatment seekers, or quick-fix weight-loss audiences.

## Content Strategy

Primary surfaces are TikTok, Instagram Reels, and YouTube Shorts. Content should lead with a visible constraint, show one short action, and end with a repeatable payoff. Carousels work for modification menus and saveable checklists. Story sequences work for daily cues and low-pressure reminders. Out-of-scope formats include long medical explainers, transformation challenges, aggressive calorie content, and platform-specific publishing tactics.

Research should look for hooks, first-frame patterns, caption language, and demonstration pacing in beginner mobility and desk wellness. Trend claims must be dated and sourced. Strategy should be revisited after each research pack or whenever the user changes the audience, surfaces, or medium scope.

## Content Pillars

### Desk Resets

- Job: turn stiffness into one visible action.
- Audience reason: viewers can act before a meeting starts.
- Example post types: shoulder reset, chair twist, wall reach, breathing cue.
- Evidence or source basis: setup fixture; current platform evidence still required.
- Priority: primary.

### Two-Minute Mobility

- Job: make short routines feel legitimate.
- Audience reason: reduces all-or-nothing thinking.
- Example post types: timer routine, three-move sequence, afternoon slump reset.
- Evidence or source basis: setup fixture.
- Priority: primary.

### Habit Cues

- Job: connect movement to existing workday moments.
- Audience reason: viewers need reminders that do not require a new identity.
- Example post types: calendar gap cue, water refill cue, end-of-day reset.
- Evidence or source basis: setup fixture.
- Priority: secondary.

## Surface Strategy

### TikTok

Role: fast testing surface for hooks and short demonstrations. Formats should be 15-35 second reset videos and comment replies. What works there is a clear first frame, immediate action, and a payoff viewers can copy. Do not chase pain-cure trends or shame hooks.

### Instagram Reels

Role: polished saveable demonstrations. Formats include Reels, carousels, and story reminders. What works there is calm visual clarity and concise overlay text. Do not make the brand look like luxury wellness.

### YouTube Shorts

Role: evergreen searchable resets. Formats should use direct titles and visible modifications. Avoid audio-dependent trends that obscure the instruction.

## Medium Strategy

### Video

Video is primary because the value is seeing the exact movement and scale. Required references include character identity, room setup, outfit, brand system, and video style. Quality bar: readable movement, safe framing, clear modifications, and no exaggerated outcomes.

### Carousel

Carousels support modifications, checklists, and "choose one" menus. They need a slide system, text overlay policy, and brand reference before regular use.

### Text

Text appears as captions, disclaimers, and comment replies. It must be concise, body-neutral, and careful around medical boundaries.

## Monetization And Partnerships

Allowed categories include mats, simple desk accessories, timers, water bottles, beginner-friendly bands, mobility education, and ordinary home fitness basics. Prohibited categories include weight-loss supplements, medical devices with inflated claims, exploitative productivity products, unsafe equipment, and anything that requires fear or shame. Disclosure must be plain in the caption or script. Acceptance test: would Luna still recommend the item if the viewer only wanted one small reset and no transformation promise?

## Boundaries And Safety

Privacy boundaries: no real address, employer, private health history, or identifiable clients. Claims boundaries: no diagnosis, treatment, pain relief promises, weight-loss promises, or medical certainty. Legal, medical, and financial limits: refer viewers to qualified professionals for pain, injury, pregnancy, surgery recovery, disability-specific modifications, or medical conditions. Cultural respect: do not borrow clinical, spiritual, or disability language as aesthetic decoration.

## Growth Goals

Trust goal: become a reliable source for calm beginner resets. Audience goal: attract viewers who save, repeat, and adapt tiny routines. Business goal: support ethical partnerships without pressure funnels. Creative goal: build a repeatable visual world around ordinary rooms and real constraints. Do not optimize for shame comments, miracle claims, or aggressive transformation stories.

## Source Notes

- source_luna_fit_breakdown_001: generated setup fixture for readiness validation.
""",
    "brand_context/voice-samples.md": """
## Status

- Source status: generated_from_intake
- Confidence: high
- Foundation accepted: yes
- Enrichment needed: none for readiness fixture.

## Samples

### 1. Workday Hook

Text: "If your next meeting starts in two minutes, good. That is the whole container."

- Why it matters: lowers the action size immediately.
- Voice signal: calm, practical, second person.
- Content mode: short-form hook
- Source: source_luna_fit_breakdown_001
- Confidence: low

### 2. Chair Reset

Text: "Keep the chair. Keep the socks. We are only asking your shoulders to remember they are not earrings."

- Why it matters: shows humor without shaming.
- Voice signal: warm image, ordinary setup.
- Content mode: voiceover
- Source: source_luna_fit_breakdown_001
- Confidence: low

### 3. Safety Boundary

Text: "If this hurts, stop and ask someone qualified. Internet confidence is not a treatment plan."

- Why it matters: preserves the medical boundary.
- Voice signal: direct, caring, plain.
- Content mode: comment reply
- Source: source_luna_fit_breakdown_001
- Confidence: low

### 4. Caption

Text: "Tiny counts when tiny is what you can repeat. Save the reset you will actually do tomorrow."

- Why it matters: defines the brand's anti-shame logic.
- Voice signal: concise encouragement.
- Content mode: caption
- Source: source_luna_fit_breakdown_001
- Confidence: low

### 5. Close

Text: "That was not a workout audition. That was a reset. Drink water and go back gently."

- Why it matters: closes with relief instead of pressure.
- Voice signal: body-neutral, calming, slightly playful.
- Content mode: video close
- Source: source_luna_fit_breakdown_001
- Confidence: low
""",
}


def rewrite_json(path, mutate):
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2) + "\n")


def remove_prompt_file(workspace_dir, relative_path):
    prompt_path = workspace_dir / relative_path
    if prompt_path.exists():
        prompt_path.unlink()


def revoke_setup_reference_generation(plan):
    plan["setup_reference_generation"] = {
        "status": "not_authorized",
        "asset_ids": [],
        "max_calls": 0,
        "authorized_on": None,
        "authorized_by": None,
        "notice": "Visual Continuity Plan is not approved.",
    }


def init_workspace_with_status(temp_dir, status):
    manifest = json.loads((ROOT / "examples" / "creator-workspace.example.json").read_text())
    manifest["status"] = status
    manifest_path = Path(temp_dir) / "creator-workspace.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    workspace_dir = init_creator(manifest_path, workspace_root=Path(temp_dir) / "creators")
    (workspace_dir / "creator-profile.json").write_text(
        (ROOT / "examples" / "creator-profile.example.json").read_text()
    )
    (workspace_dir / "references" / "reference-library.json").write_text(
        (ROOT / "examples" / "reference-library.example.json").read_text()
    )
    (workspace_dir / "references" / "visual-continuity-plan.json").write_text(
        (ROOT / "examples" / "visual-continuity-plan.example.json").read_text()
    )
    (workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md").write_text(
        (ROOT / "examples" / "sources" / "luna-fit-breakdown.example.md").read_text()
    )
    for relative_path in (
        "brand_context/identity.md",
        "brand_context/soul.md",
        "brand_context/personal-brand.md",
        "references/character/luna-identity-plate.png",
    ):
        path = workspace_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("review packet fixture\n")
    board_path = workspace_dir / "references" / "brand" / "personal-brand-board.json"
    board_path.parent.mkdir(parents=True, exist_ok=True)
    board_path.write_text(
        json.dumps({"avatar_asset_id": "asset_luna_identity_plate"}) + "\n"
    )
    review = json.loads((ROOT / "examples" / "review-record.example.json").read_text())
    review.pop("project_id")
    review.pop("concept_approval_id")
    review.update(
        review_record_id="review_luna_setup_001",
        review_role="setup",
        artifact_refs=[
            "creator-profile.json",
            "brand_context/identity.md",
            "brand_context/soul.md",
            "brand_context/personal-brand.md",
            "references/reference-library.json",
            "references/character/luna-identity-plate.png",
            "references/visual-continuity-plan.json",
        ],
    )
    review["findings"] = [
        {
            "area": "foundation",
            "severity": "none",
            "note": "The fixture foundation is internally consistent.",
        }
    ]
    review["reviewer_execution"]["source_skill"] = "review-creator-setup"
    reviews_dir = workspace_dir / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    (reviews_dir / f"{review['review_record_id']}.json").write_text(
        json.dumps(review, indent=2) + "\n"
    )
    return workspace_dir


def populate_foundation(workspace_dir):
    for relative_path, sample in FOUNDATION_SAMPLE.items():
        target = workspace_dir / relative_path
        target.write_text(target.read_text() + sample)


def place_asset_files(workspace_dir):
    library = json.loads((workspace_dir / "references" / "reference-library.json").read_text())
    for asset in library["assets"]:
        if asset["asset_status"] in {"user_provided", "generated", "approved"}:
            target = workspace_dir / asset["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"placeholder for {asset['asset_id']}\n")
        if asset.get("prompt_path"):
            prompt = workspace_dir / asset["prompt_path"]
            prompt.parent.mkdir(parents=True, exist_ok=True)
            prompt.write_text(f"prompt for {asset['asset_id']}\n")


def place_brand_board_space_files(workspace_dir):
    spec_path = workspace_dir / "references" / "brand" / "personal-brand-board.json"
    if not spec_path.exists():
        return
    spec = json.loads(spec_path.read_text())
    library = json.loads(
        (workspace_dir / "references" / "reference-library.json").read_text()
    )
    assets_by_id = {asset["asset_id"]: asset for asset in library["assets"]}
    for item in [*spec["production_spaces"], *spec["signature_props"]]:
        target = workspace_dir / assets_by_id[item["reference_asset_id"]]["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"brand board reference fixture for {item['title']}\n")


def write_readiness_milestones(
    workspace_dir,
    profile_status="ready",
    foundation_status="ready",
    foundation_mode="prompt_ready",
    strategy_status="not_started",
    production_status="not_started",
    image_allowed=False,
    video_allowed=False,
    spoken_allowed=False,
):
    record = json.loads((ROOT / "examples" / "readiness-gates.example.json").read_text())
    record["milestones"]["profile"]["status"] = profile_status
    record["milestones"]["foundation"]["status"] = foundation_status
    record["milestones"]["foundation"]["mode"] = foundation_mode
    record["milestones"]["strategy"]["status"] = strategy_status
    record["milestones"]["production"]["status"] = production_status
    for milestone in record["milestones"].values():
        if milestone["status"] == "ready":
            milestone["approved_on"] = "2026-07-09"
            milestone["approved_by"] = "user"
            milestone["blockers"] = []
        else:
            milestone["approved_on"] = None
            milestone["approved_by"] = None
            milestone["blockers"] = ["Milestone is not ready."]
    production = record["milestones"]["production"]
    production["terminal_review_record_id"] = (
        "review_luna_strategy_001" if production_status == "ready" else None
    )
    record["permissions"] = {
        "creator_image_generation_allowed": image_allowed,
        "creator_video_generation_allowed": video_allowed,
        "spoken_voice_generation_allowed": spoken_allowed,
    }
    (workspace_dir / "readiness-gates.json").write_text(json.dumps(record, indent=2) + "\n")
    if production_status == "ready":
        _write_terminal_strategy_review(workspace_dir)


def _write_terminal_strategy_review(workspace_dir):
    findings_path = workspace_dir / "research" / "findings.md"
    findings_path.parent.mkdir(parents=True, exist_ok=True)
    findings_path.write_text("# Research Findings\n\nStrategy review fixture.\n")
    evidence_path = (
        workspace_dir
        / "research"
        / "runs"
        / "research_run_luna_strategy_001"
        / "evidence.jsonl"
    )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text('{"evidence_id":"evidence_luna_strategy_001"}\n')
    review = json.loads((ROOT / "examples" / "review-record.example.json").read_text())
    review.pop("project_id")
    review.pop("concept_approval_id")
    review.update(
        review_record_id="review_luna_strategy_001",
        review_role="strategy",
        artifact_refs=[
            "creator-profile.json",
            "content-strategy.json",
            "content-schedule.json",
            "research/findings.md",
            "research/runs/research_run_luna_strategy_001/evidence.jsonl",
        ],
        findings=[
            {
                "area": "strategy",
                "severity": "none",
                "note": "The fixture strategy is internally consistent.",
            }
        ],
    )
    review["reviewer_execution"]["source_skill"] = "review-strategy"
    reviews_dir = workspace_dir / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    (reviews_dir / "review_luna_strategy_001.json").write_text(
        json.dumps(review, indent=2) + "\n"
    )


def write_channels(workspace_dir):
    record = json.loads((ROOT / "examples" / "channels.example.json").read_text())
    record["channels"][1].update(
        channel_id="channel_luna_fit_tiktok",
        platform="tiktok",
        intended_handle="@lunafit",
        public_url="https://www.tiktok.com/@lunafit",
        account_status="created",
        publishing_export_blocked=False,
        notes="Short-form testing channel.",
    )
    (workspace_dir / "channels.json").write_text(json.dumps(record, indent=2) + "\n")


def write_content_strategy(workspace_dir, status="approved"):
    record = json.loads((ROOT / "examples" / "content-strategy.example.json").read_text())
    record["strategy_status"] = status
    (workspace_dir / "content-strategy.json").write_text(json.dumps(record, indent=2) + "\n")


def write_conversion_asset(workspace_dir, status="approved"):
    record = json.loads((ROOT / "examples" / "conversion-asset.example.json").read_text())
    record["status"] = status
    if status in {"planned", "drafted"}:
        record["approval"] = {
            "status": "pending",
            "approved_by": None,
            "approved_on": None,
            "notes": "Awaiting user review of the final conversion asset.",
        }
    target = workspace_dir / "conversion-assets" / f"{record['conversion_asset_id']}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2) + "\n")
    markdown = workspace_dir / "conversion-assets" / "luna-reset-checklist.md"
    markdown.write_text("# 7 Tiny Reset Questions\n")


def write_content_schedule(workspace_dir, *, research_informed=True):
    record = json.loads((ROOT / "examples" / "creator-content-schedule.example.json").read_text())
    if research_informed:
        run_id = "research_run_luna_schedule_001"
        record["research_basis"] = {
            "status": "research_informed",
            "research_run_ids": [run_id],
        }
        run_dir = workspace_dir / "research" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        run = {
            "research_run_id": run_id,
            "creator_profile_id": "creator_luna_fit",
            "started_on": "2026-07-02T10:00:00",
            "completed_on": "2026-07-02T11:00:00",
            "mode": "scheduled_needs",
            "scope": "Validate the first production calendar topics.",
            "schedule_slot_ids": [],
            "platforms": ["instagram"],
            "material_update": False,
            "outputs": {
                "finding_ids": [],
                "content_opportunity_ids": [],
                "evidence_ids": [],
                "metric_snapshot_ids": [],
                "research_intelligence_updates": [],
            },
            "run_status": "completed_no_material_update",
        }
        (run_dir / "research-run.json").write_text(json.dumps(run, indent=2) + "\n")
    (workspace_dir / "content-schedule.json").write_text(json.dumps(record, indent=2) + "\n")


def make_ready_workspace(temp_dir, status):
    workspace_dir = init_workspace_with_status(temp_dir, status)
    populate_foundation(workspace_dir)
    place_asset_files(workspace_dir)
    write_readiness_milestones(workspace_dir)
    write_channels(workspace_dir)
    write_content_strategy(workspace_dir, status="approved")
    if status in {"strategy_ready", "production_ready", "active"}:
        write_content_schedule(
            workspace_dir,
            research_informed=status in {"production_ready", "active"},
        )
    write_conversion_asset(workspace_dir)
    (workspace_dir / "references" / "brand" / "personal-brand-board.json").write_text(
        (ROOT / "examples" / "personal-brand-board.example.json").read_text()
    )
    place_brand_board_space_files(workspace_dir)
    rebuild_brand_board(workspace_dir)
    return workspace_dir


class DraftLenienceTests(unittest.TestCase):
    def test_draft_workspace_with_scaffold_foundation_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_draft_workspace_rejects_conversion_asset_from_another_strategy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            write_conversion_asset(workspace_dir, status="drafted")

            def mismatch_strategy(asset):
                asset["source_content_strategy_id"] = "content_strategy_wrong"

            rewrite_json(
                workspace_dir
                / "conversion-assets"
                / "conversion_asset_luna_reset_checklist.json",
                mismatch_strategy,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("source_content_strategy_id", str(ctx.exception))

    def test_draft_workspace_rejects_a_falsely_ready_milestone_without_human_approval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")

            def falsely_mark_ready(readiness):
                readiness["milestones"]["profile"]["status"] = "ready"
                readiness["milestones"]["profile"]["approved_on"] = None
                readiness["milestones"]["profile"]["approved_by"] = None

            rewrite_json(workspace_dir / "readiness-gates.json", falsely_mark_ready)

            with self.assertRaisesRegex(ValidationError, "user approval metadata"):
                validate_creator_workspace(workspace_dir)

    def test_draft_workspace_rejects_contradictory_channel_export_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")

            def unblock_missing_account(channels):
                channels["channels"][0]["account_status"] = "not_created"
                channels["channels"][0]["publishing_export_blocked"] = False

            rewrite_json(workspace_dir / "channels.json", unblock_missing_account)

            with self.assertRaisesRegex(ValidationError, "publishing_export_blocked"):
                validate_creator_workspace(workspace_dir)

    def test_draft_workspace_rejects_prompt_ready_media_permission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")

            def contradict_prompt_mode(readiness):
                readiness["milestones"]["foundation"]["mode"] = "prompt_ready"
                readiness["permissions"]["creator_image_generation_allowed"] = True

            rewrite_json(workspace_dir / "readiness-gates.json", contradict_prompt_mode)

            with self.assertRaisesRegex(ValidationError, "prompt_ready.*permissions.*false"):
                validate_creator_workspace(workspace_dir)


class OnboardingReadinessMilestoneTests(unittest.TestCase):
    def test_deprecated_workspace_status_warns_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")

            def use_deprecated_status(manifest):
                manifest["status"] = "content_ready"

            rewrite_json(workspace_dir / "creator-workspace.json", use_deprecated_status)

            result = validate_creator_workspace(workspace_dir)

            self.assertTrue(any("deprecated status 'content_ready'" in warning for warning in result["warnings"]))

    def test_profile_ready_requires_selected_channels_in_registry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "profile_ready")
            (workspace_dir / "creator-profile.json").write_text(
                (ROOT / "examples" / "creator-profile.example.json").read_text()
            )
            (workspace_dir / "references" / "reference-library.json").write_text(
                (ROOT / "examples" / "reference-library.example.json").read_text()
            )
            (workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md").write_text(
                (ROOT / "examples" / "sources" / "luna-fit-breakdown.example.md").read_text()
            )
            write_readiness_milestones(workspace_dir, foundation_status="not_started")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("selected channel", str(ctx.exception))
            self.assertIn("tiktok", str(ctx.exception))

    def test_foundation_ready_requires_ready_foundation_milestone(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            write_readiness_milestones(
                workspace_dir,
                foundation_status="blocked",
                foundation_mode="prompt_ready",
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("foundation readiness milestone", str(ctx.exception))

    def test_creator_video_permission_requires_approved_visual_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            write_readiness_milestones(workspace_dir, foundation_mode="media_ready", video_allowed=True)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("creator_video_generation_allowed", message)
            self.assertIn("approved visual identity", message)

    def test_spoken_voice_permission_rejects_approved_voice_design_prompt_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            write_readiness_milestones(workspace_dir, spoken_allowed=True)

            def approve_voice_design_prompt(library):
                for asset in library["assets"]:
                    if asset["asset_id"] == "asset_luna_elevenlabs_voice_design":
                        asset["asset_status"] = "approved"

            rewrite_json(
                workspace_dir / "references" / "reference-library.json",
                approve_voice_design_prompt,
            )
            place_asset_files(workspace_dir)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("approved/imported voice reference", str(ctx.exception))

    def test_prompt_ready_foundation_rejects_all_creator_media_permissions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            write_readiness_milestones(
                workspace_dir,
                foundation_mode="prompt_ready",
                image_allowed=True,
            )

            with self.assertRaisesRegex(ValidationError, "prompt_ready.*permissions.*false"):
                validate_creator_workspace(workspace_dir)

    def test_media_ready_video_foundation_does_not_require_voice_when_spoken_generation_is_disabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            write_readiness_milestones(workspace_dir, foundation_mode="media_ready", spoken_allowed=False)

            def approve_visual_assets(library):
                for asset in library["assets"]:
                    if asset["asset_type"] != "voice":
                        asset["asset_status"] = "approved"

            rewrite_json(
                workspace_dir / "references" / "reference-library.json",
                approve_visual_assets,
            )
            place_asset_files(workspace_dir)
            rebuild_brand_board(workspace_dir)

            result = validate_creator_workspace(workspace_dir)

            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_ready_readiness_milestone_requires_human_approval_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "profile_ready")

            def remove_approval_metadata(readiness):
                readiness["milestones"]["profile"]["approved_on"] = None
                readiness["milestones"]["profile"]["approved_by"] = None

            rewrite_json(workspace_dir / "readiness-gates.json", remove_approval_metadata)

            with self.assertRaisesRegex(ValidationError, "user approval metadata"):
                validate_creator_workspace(workspace_dir)

    def test_strategy_ready_requires_approved_strategy_and_conversion_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready")
            write_content_strategy(workspace_dir, status="drafted")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("content-strategy.json", str(ctx.exception))
            self.assertIn("approved", str(ctx.exception))

    def test_strategy_ready_allows_a_drafted_conversion_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready")
            write_conversion_asset(workspace_dir, status="drafted")

            result = validate_creator_workspace(workspace_dir)

            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_strategy_ready_rejects_conversion_asset_from_another_creator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready")

            def mismatch_creator(asset):
                asset["creator_profile_id"] = "creator_wrong"
                asset["creator_slug"] = "wrong-creator"

            rewrite_json(
                workspace_dir
                / "conversion-assets"
                / "conversion_asset_luna_reset_checklist.json",
                mismatch_creator,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("creator_profile_id", str(ctx.exception))

    def test_strategy_ready_rejects_conversion_asset_from_another_strategy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready")

            def mismatch_strategy(asset):
                asset["source_content_strategy_id"] = "content_strategy_wrong"

            rewrite_json(
                workspace_dir
                / "conversion-assets"
                / "conversion_asset_luna_reset_checklist.json",
                mismatch_strategy,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("source_content_strategy_id", str(ctx.exception))
            self.assertIn("accepted strategy", str(ctx.exception))

    def test_approved_conversion_asset_requires_explicit_user_approval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready")

            def remove_user_approval(asset):
                asset["approval"] = {
                    "status": "pending",
                    "approved_by": None,
                    "approved_on": None,
                    "notes": "Rendered but not reviewed.",
                }

            rewrite_json(
                workspace_dir
                / "conversion-assets"
                / "conversion_asset_luna_reset_checklist.json",
                remove_user_approval,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("user_approved", str(ctx.exception))

    def test_strategy_ready_requires_conversion_asset_file_refs_to_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready")
            (workspace_dir / "conversion-assets" / "luna-reset-checklist.md").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("conversion asset", str(ctx.exception))
            self.assertIn("file_refs", str(ctx.exception))

    def test_strategy_ready_rejects_dangling_variant_refs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready")

            def dangle_variants(strategy):
                strategy["monthly_mix"][0]["variant_id"] = "variant_missing_mix"
                strategy["content_series"][0]["anchor_variant"] = "variant_missing_anchor"
                strategy["content_series"][0]["derivative_variants"] = [
                    "variant_missing_derivative"
                ]

            rewrite_json(workspace_dir / "content-strategy.json", dangle_variants)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("variant", str(ctx.exception))

    def test_production_ready_requires_content_schedule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(
                workspace_dir,
                strategy_status="ready",
                production_status="ready",
            )
            (workspace_dir / "content-schedule.json").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("content-schedule.json", str(ctx.exception))

    def test_production_ready_rejects_strategy_scaffold(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(
                workspace_dir,
                strategy_status="ready",
                production_status="ready",
            )
            write_content_schedule(workspace_dir, research_informed=False)

            with self.assertRaisesRegex(ValidationError, "strategy_scaffold.*complete research"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_rejects_missing_schedule_research_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(
                workspace_dir,
                strategy_status="ready",
                production_status="ready",
            )
            write_content_schedule(workspace_dir)
            run_path = (
                workspace_dir
                / "research"
                / "runs"
                / "research_run_luna_schedule_001"
                / "research-run.json"
            )
            run_path.unlink()

            with self.assertRaisesRegex(ValidationError, "missing research run"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_rejects_schedule_for_another_creator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_content_schedule(workspace_dir)

            def mismatch_creator(schedule):
                schedule["creator_profile_id"] = "creator_wrong"

            rewrite_json(workspace_dir / "content-schedule.json", mismatch_creator)

            with self.assertRaisesRegex(ValidationError, "creator_profile_id"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_rejects_schedule_for_another_strategy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_content_schedule(workspace_dir)
            rewrite_json(
                workspace_dir / "content-schedule.json",
                lambda schedule: schedule.update(content_strategy_id="content_strategy_wrong"),
            )

            with self.assertRaisesRegex(ValidationError, "content_strategy_id"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_requires_slot_strategy_relationships_to_agree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_content_schedule(workspace_dir)

            def contradict_strategy(strategy):
                strategy["content_series"][0]["conversion_asset_ids"] = []

            def contradict_variant(schedule):
                schedule["calendar_slots"][0]["variant_id"] = (
                    "variant_luna_claim_teardown_linkedin_text"
                )

            rewrite_json(workspace_dir / "content-strategy.json", contradict_strategy)
            rewrite_json(workspace_dir / "content-schedule.json", contradict_variant)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("variant platform 'linkedin' does not match slot platform 'instagram'", message)
            self.assertIn("variant format 'format_thread' does not match slot format 'format_short_form_video'", message)
            self.assertIn("conversion asset", message)
            self.assertIn("does not belong to content series", message)

    def test_production_ready_requires_at_least_one_calendar_slot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_content_schedule(workspace_dir)
            rewrite_json(workspace_dir / "content-schedule.json", lambda schedule: schedule["calendar_slots"].clear())

            with self.assertRaisesRegex(ValidationError, "calendar slot"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_rejects_dangling_content_goal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_content_schedule(workspace_dir)
            rewrite_json(
                workspace_dir / "content-schedule.json",
                lambda schedule: schedule["calendar_slots"][0].update(content_goal_id="goal_missing"),
            )

            with self.assertRaisesRegex(ValidationError, "missing content goal"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_rejects_unapproved_promoted_conversion_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_conversion_asset(workspace_dir, status="drafted")
            write_content_schedule(workspace_dir)

            with self.assertRaisesRegex(ValidationError, "drafted.*approved"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_requires_channel_approval_for_scheduled_platform(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_content_schedule(workspace_dir)

            def disallow_instagram_production(channels):
                channels["channels"][0]["production_drafting_allowed"] = False

            rewrite_json(workspace_dir / "channels.json", disallow_instagram_production)

            with self.assertRaisesRegex(ValidationError, "not approved for production drafting"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_requires_every_slot_to_name_a_platform(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_content_schedule(workspace_dir)

            def remove_platform_and_conversion(schedule):
                slot = schedule["calendar_slots"][0]
                slot.pop("platform")
                slot.pop("conversion_asset_ids")
                slot.pop("conversion_use")

            rewrite_json(workspace_dir / "content-schedule.json", remove_platform_and_conversion)

            with self.assertRaisesRegex(ValidationError, "must name a platform"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_requires_explicit_skip_when_channel_account_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_content_schedule(workspace_dir)

            def leave_instagram_uncreated(channels):
                channels["channels"][0].update(
                    account_status="not_created",
                    publishing_export_blocked=True,
                )

            rewrite_json(workspace_dir / "channels.json", leave_instagram_uncreated)

            with self.assertRaisesRegex(ValidationError, "explicit skip"):
                validate_creator_workspace(workspace_dir)

    def test_production_ready_requires_conversion_asset_approval_for_use_and_platform(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready", production_status="ready")
            write_content_schedule(workspace_dir)

            def remove_slot_approval(asset):
                asset["approved_uses"] = ["email_capture"]
                asset["platforms"] = ["linkedin"]

            rewrite_json(
                workspace_dir / "conversion-assets" / "conversion_asset_luna_reset_checklist.json",
                remove_slot_approval,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("not approved for use 'soft_cta'", str(ctx.exception))
            self.assertIn("not approved for platform instagram", str(ctx.exception))

    def test_channel_without_account_cannot_claim_export_is_unblocked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "profile_ready")

            def contradict_account_state(channels):
                channels["channels"][0]["account_status"] = "skipped"
                channels["channels"][0]["publishing_export_blocked"] = False

            rewrite_json(workspace_dir / "channels.json", contradict_account_state)

            with self.assertRaisesRegex(ValidationError, "publishing_export_blocked"):
                validate_creator_workspace(workspace_dir)

    def test_prompt_ready_and_skipped_handle_are_reported_as_warnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def skip_account(channels):
                channels["channels"][0].update(
                    account_status="skipped",
                    intended_handle=None,
                    public_url=None,
                    publishing_export_blocked=True,
                    notes="Account setup intentionally skipped for now.",
                )

            rewrite_json(workspace_dir / "channels.json", skip_account)

            result = validate_creator_workspace(workspace_dir)

            self.assertTrue(any("prompt_ready" in warning for warning in result["warnings"]))
            self.assertTrue(any("skipped" in warning and "handle" in warning for warning in result["warnings"]))

    def test_strategy_ready_without_calendar_slots_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")
            write_readiness_milestones(workspace_dir, strategy_status="ready")
            (workspace_dir / "content-schedule.json").unlink()

            with self.assertRaisesRegex(
                ValidationError, "complete content-schedule.json strategy scaffold"
            ):
                validate_creator_workspace(workspace_dir)

    def test_strategy_ready_rejects_calendar_below_monthly_mix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")

            def require_two(strategy):
                strategy["monthly_mix"][0]["target_count_per_month"] = 2

            rewrite_json(workspace_dir / "content-strategy.json", require_two)

            with self.assertRaisesRegex(ValidationError, "requires 2 slot.*found 1"):
                validate_creator_workspace(workspace_dir)

    def test_strategy_ready_rejects_unapproved_calendar(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "strategy_ready")

            def reopen(schedule):
                schedule["approval"] = {
                    "status": "pending",
                    "approved_by": None,
                    "approved_on": None,
                }

            rewrite_json(workspace_dir / "content-schedule.json", reopen)

            with self.assertRaisesRegex(ValidationError, "explicit user approval"):
                validate_creator_workspace(workspace_dir)

    def test_foundation_ready_rejects_stale_foundation_blocker_prose(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            (workspace_dir / "brand_context" / "identity.md").write_text(
                (workspace_dir / "brand_context" / "identity.md").read_text()
                + "\n- Open blockers: user approval of the generated portrait concept.\n"
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("stale foundation blocker language", message)
            self.assertIn("brand_context/identity.md", message)

    def test_foundation_ready_rejects_stale_soul_blocker_prose(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            (workspace_dir / "brand_context" / "soul.md").write_text(
                (workspace_dir / "brand_context" / "soul.md").read_text()
                + "\n- Open blockers: portrait pending approval.\n"
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("stale foundation blocker language", message)
            self.assertIn("brand_context/soul.md", message)

    def test_foundation_ready_allows_negated_reference_asset_phrase(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            (workspace_dir / "progress" / "setup-checklist.md").write_text(
                (workspace_dir / "progress" / "setup-checklist.md").read_text()
                + "\n- No reference assets missing after approval.\n"
            )

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_mara_style_state_stays_blocked_before_production(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "production_ready")
            write_readiness_milestones(
                workspace_dir,
                strategy_status="ready",
                production_status="ready",
            )
            write_conversion_asset(workspace_dir, status="drafted")
            write_content_schedule(workspace_dir)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("conversion asset", message)
            self.assertIn("drafted", message)


class ReferenceLibraryIntegrityTests(unittest.TestCase):
    def test_setup_generation_authorization_rejects_unknown_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def add_unknown(plan):
                authorization = plan["setup_reference_generation"]
                authorization["asset_ids"].append("asset_luna_unknown")
                authorization["max_calls"] = len(authorization["asset_ids"])

            rewrite_json(
                workspace_dir / "references" / "visual-continuity-plan.json",
                add_unknown,
            )
            with self.assertRaisesRegex(ValueError, "do not resolve"):
                validate_creator_workspace(workspace_dir)

    def test_setup_generation_authorization_rejects_non_image_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def add_voice(plan):
                authorization = plan["setup_reference_generation"]
                authorization["asset_ids"].append("asset_luna_elevenlabs_voice_design")
                authorization["max_calls"] = len(authorization["asset_ids"])

            rewrite_json(
                workspace_dir / "references" / "visual-continuity-plan.json",
                add_voice,
            )
            with self.assertRaisesRegex(ValueError, "image assets only"):
                validate_creator_workspace(workspace_dir)

    def test_approved_visual_plan_authorizes_one_call_per_listed_setup_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            plan_path = workspace_dir / "references" / "visual-continuity-plan.json"

            def mismatch_call_cap(plan):
                plan["setup_reference_generation"]["max_calls"] -= 1

            rewrite_json(plan_path, mismatch_call_cap)

            with self.assertRaisesRegex(ValueError, "one call per listed asset"):
                validate_creator_workspace(workspace_dir)

    def test_approved_visual_plan_generation_package_rejects_board_avatar(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            plan_path = workspace_dir / "references" / "visual-continuity-plan.json"
            library_path = workspace_dir / "references" / "reference-library.json"

            def mark_avatar_pending(library):
                avatar = next(
                    asset for asset in library["assets"]
                    if asset["asset_id"] == "asset_luna_identity_plate"
                )
                avatar["asset_status"] = "prompted"
                avatar["prompt_path"] = "references/character/luna-avatar.prompt.md"

            rewrite_json(library_path, mark_avatar_pending)
            (workspace_dir / "references" / "character" / "luna-avatar.prompt.md").write_text(
                "Generate the approved avatar.\n"
            )

            def include_avatar(plan):
                authorization = plan["setup_reference_generation"]
                authorization["asset_ids"].append("asset_luna_identity_plate")
                authorization["max_calls"] = len(authorization["asset_ids"])

            rewrite_json(plan_path, include_avatar)

            with self.assertRaisesRegex(ValueError, "exclude designated brand-board avatar"):
                validate_creator_workspace(workspace_dir)

    def test_visual_foundation_readiness_requires_presented_and_approved_candidates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "foundation_ready")
            plan_path = workspace_dir / "references" / "visual-continuity-plan.json"

            def leave_review_pending(plan):
                revoke_setup_reference_generation(plan)
                plan["selection_review"] = {
                    "status": "pending_user_review",
                    "presented_on": "2026-07-09",
                    "decided_on": None,
                    "decided_by": None,
                    "terminal_review_record_id": None,
                    "notes": "Candidates were presented and await the user's decision.",
                }
                for candidate in plan["candidates"]:
                    candidate["user_decision"] = "pending"
                    candidate["decision_notes"] = "Awaiting the user's decision."

            rewrite_json(plan_path, leave_review_pending)
            rewrite_json(
                workspace_dir / "references" / "reference-library.json",
                lambda library: library.update(
                    assets=[
                        asset
                        for asset in library["assets"]
                        if asset["asset_type"] not in {"object", "location"}
                    ]
                ),
            )
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["reference_refs"].update(
                    primary_location_asset_ids=[]
                ),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("foundation_ready", str(ctx.exception))
            self.assertIn("user-approved Visual Continuity Plan", str(ctx.exception))

    def test_reference_assets_wait_for_visual_continuity_user_approval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            plan = json.loads(
                (ROOT / "examples" / "visual-continuity-plan.example.json").read_text()
            )
            plan["selection_review"] = {
                "status": "pending_user_review",
                "presented_on": "2026-07-09",
                "decided_on": None,
                "decided_by": None,
                "terminal_review_record_id": None,
                "notes": "Candidate props and production spaces are awaiting user review."
            }
            revoke_setup_reference_generation(plan)
            for candidate in plan["candidates"]:
                candidate["user_decision"] = "pending"
                candidate["decision_notes"] = "Awaiting the user's decision."
            (workspace_dir / "references" / "visual-continuity-plan.json").write_text(
                json.dumps(plan, indent=2) + "\n"
            )

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("Visual Continuity Plan", str(ctx.exception))
            self.assertIn("user-approved", str(ctx.exception))

    def test_orphan_object_or_location_prompt_waits_for_user_approval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            plan_path = workspace_dir / "references" / "visual-continuity-plan.json"
            plan = json.loads(plan_path.read_text())
            plan["selection_review"] = {
                "status": "pending_user_review",
                "presented_on": "2026-07-09",
                "decided_on": None,
                "decided_by": None,
                "terminal_review_record_id": None,
                "notes": "Candidate selection is awaiting user review."
            }
            revoke_setup_reference_generation(plan)
            for candidate in plan["candidates"]:
                candidate["user_decision"] = "pending"
                candidate["decision_notes"] = "Awaiting user review."
            plan_path.write_text(json.dumps(plan, indent=2) + "\n")
            rewrite_json(
                workspace_dir / "references" / "reference-library.json",
                lambda library: library.update(
                    assets=[
                        asset
                        for asset in library["assets"]
                        if asset["asset_type"] not in {"object", "location"}
                    ]
                ),
            )
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["reference_refs"].update(
                    primary_location_asset_ids=[]
                ),
            )
            orphan = workspace_dir / "references" / "props" / "unapproved.prompt.md"
            orphan.parent.mkdir(parents=True, exist_ok=True)
            orphan.write_text("Unapproved object prompt.\n")

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("unapproved.prompt.md", str(ctx.exception))
            self.assertIn("user-approved", str(ctx.exception))

    def test_approved_plan_rejects_prompt_without_declared_selected_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            orphan = workspace_dir / "references" / "props" / "rejected-prop.prompt.md"
            orphan.parent.mkdir(parents=True, exist_ok=True)
            orphan.write_text("Prompt for a prop the user rejected.\n")

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("rejected-prop.prompt.md", str(ctx.exception))
            self.assertIn("declared Reference Assets", str(ctx.exception))

    def test_visual_continuity_source_refs_must_resolve_inside_workspace(self):
        for bad_ref in ("sources/intakes/missing.md#object", "../../outside.md#object"):
            with self.subTest(bad_ref=bad_ref), tempfile.TemporaryDirectory() as temp_dir:
                workspace_dir = init_workspace_with_status(temp_dir, "draft")
                rewrite_json(
                    workspace_dir / "references" / "visual-continuity-plan.json",
                    lambda plan: plan["candidates"][0].update(source_refs=[bad_ref]),
                )

                with self.assertRaises(ValueError) as ctx:
                    validate_creator_workspace(workspace_dir)
                self.assertIn("source_ref", str(ctx.exception))
                self.assertIn(bad_ref, str(ctx.exception))

    def test_nonvisual_plan_still_rejects_duplicate_candidate_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["content_strategy"].update(
                    content_mediums=["text"]
                ),
            )

            def duplicate_candidate(plan):
                plan["candidates"].append(json.loads(json.dumps(plan["candidates"][0])))

            rewrite_json(
                workspace_dir / "references" / "visual-continuity-plan.json",
                duplicate_candidate,
            )

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("Duplicate Visual Continuity Plan candidate ids", str(ctx.exception))

    def test_selected_reference_asset_must_link_to_accepted_candidate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            (workspace_dir / "references" / "visual-continuity-plan.json").write_text(
                (ROOT / "examples" / "visual-continuity-plan.example.json").read_text()
            )
            rewrite_json(
                workspace_dir / "references" / "reference-library.json",
                lambda library: next(
                    asset
                    for asset in library["assets"]
                    if asset["asset_id"] == "asset_luna_living_room"
                ).pop("selection_candidate_id"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("selection_candidate_id", str(ctx.exception))
            self.assertIn("asset_luna_living_room", str(ctx.exception))

    def test_product_object_asset_can_link_to_signature_object_candidate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")

            def add_product_candidate(plan):
                candidate = json.loads(json.dumps(plan["candidates"][1]))
                candidate.update(
                    candidate_id="continuity_candidate_luna_product_bottle",
                    candidate_type="product_object",
                    name="Luna branded reset bottle",
                    recommendation="signature_object",
                    recommendation_rationale="The product and packaging need stable recognition.",
                    user_decision="accepted",
                    decision_notes="User accepted the product object.",
                    target_asset_id="asset_luna_product_bottle",
                )
                plan["candidates"].append(candidate)

            rewrite_json(
                workspace_dir / "references" / "visual-continuity-plan.json",
                add_product_candidate,
            )

            def add_product_asset(library):
                asset = json.loads(
                    json.dumps(
                        next(
                            item
                            for item in library["assets"]
                            if item["asset_id"] == "asset_luna_living_room"
                        )
                    )
                )
                asset.update(
                    asset_id="asset_luna_product_bottle",
                    asset_type="object",
                    role="Stable branded reset bottle product reference",
                    path="references/objects/luna-product-bottle.png",
                    selection_candidate_id="continuity_candidate_luna_product_bottle",
                )
                library["assets"].append(asset)

            rewrite_json(
                workspace_dir / "references" / "reference-library.json",
                add_product_asset,
            )

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_approved_plan_cannot_accept_an_unresolved_clarification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            plan_path = workspace_dir / "references" / "visual-continuity-plan.json"

            def reopen_candidate(plan):
                candidate = plan["candidates"][1]
                candidate["recommendation"] = "clarify"
                candidate["user_decision"] = "accepted"
                candidate["decision_notes"] = "Accepted without resolving the ambiguity."

            rewrite_json(plan_path, reopen_candidate)

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("clarify", str(ctx.exception))
            self.assertIn("unresolved", str(ctx.exception))

    def test_duplicate_asset_ids_are_rejected_even_at_draft(self):
        # Two assets sharing an id make every reference to that id ambiguous
        # (dict resolution is last-wins), so duplicates fail at every status.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            library_path = workspace_dir / "references" / "reference-library.json"

            def duplicate_brand_asset(library):
                clone = json.loads(
                    json.dumps(
                        next(
                            asset
                            for asset in library["assets"]
                            if asset["asset_id"] == "asset_luna_brand_system"
                        )
                    )
                )
                clone["usage_notes"] = "Conflicting duplicate of the brand system."
                library["assets"].append(clone)

            rewrite_json(library_path, duplicate_brand_asset)

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("Duplicate reference library asset ids", str(ctx.exception))
            self.assertIn("asset_luna_brand_system", str(ctx.exception))


class FoundationReadyBlockerTests(unittest.TestCase):
    def test_text_only_foundation_requires_a_complete_personal_brand_board(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def make_text_only(profile):
                profile["content_strategy"]["content_mediums"] = ["text"]

            rewrite_json(workspace_dir / "creator-profile.json", make_text_only)
            (workspace_dir / "references" / "brand" / "personal-brand-board.json").unlink()
            (workspace_dir / "references" / "brand" / "personal-brand-board.html").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("personal brand board", str(ctx.exception))

    def test_text_only_foundation_requires_explicit_personal_brand_board_approval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def make_text_only(profile):
                profile["content_strategy"]["content_mediums"] = ["text"]

            def reopen_board(spec):
                spec["approval_status"] = "draft_for_review"

            rewrite_json(workspace_dir / "creator-profile.json", make_text_only)
            rewrite_json(
                workspace_dir / "references" / "brand" / "personal-brand-board.json",
                reopen_board,
            )
            rebuild_brand_board(workspace_dir)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("personal brand board requires explicit approval", str(ctx.exception))

    def test_visual_foundation_requires_a_complete_personal_brand_board(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            (workspace_dir / "references" / "brand" / "personal-brand-board.json").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("personal brand board", str(ctx.exception))

    def test_visual_foundation_requires_explicit_personal_brand_board_approval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def reopen_board(spec):
                spec["approval_status"] = "draft_for_review"

            rewrite_json(
                workspace_dir / "references" / "brand" / "personal-brand-board.json",
                reopen_board,
            )
            rebuild_brand_board(workspace_dir)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("personal brand board requires explicit approval", str(ctx.exception))

    def test_populated_foundation_ready_workspace_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_scaffold_only_foundation_file_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            identity = workspace_dir / "brand_context" / "identity.md"
            identity.write_text("# Identity\n\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("brand_context/identity.md", str(ctx.exception))

    def test_tbd_placeholder_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            soul = workspace_dir / "brand_context" / "soul.md"
            soul.write_text(soul.read_text() + "\nHumor rules: TBD\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("TBD", str(ctx.exception))

    def test_oversized_context_file_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            soul = workspace_dir / "context" / "SOUL.md"
            soul.write_text(soul.read_text() + ("Luna keeps sessions tiny. " * 200))

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("context/SOUL.md", str(ctx.exception))
            self.assertIn("byte cap", str(ctx.exception))

    def test_sentence_stub_foundation_file_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            personal_brand = workspace_dir / "brand_context" / "personal-brand.md"
            personal_brand.write_text(
                "# Personal Brand\n\nShort-form vertical video first; no crash-diet content ever.\n"
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("brand_context/personal-brand.md", str(ctx.exception))
            self.assertIn("too thin", str(ctx.exception))

    def test_missing_required_foundation_sections_are_blockers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            personal_brand = workspace_dir / "brand_context" / "personal-brand.md"
            personal_brand.write_text(
                "# Personal Brand\n\n"
                "## Brand Snapshot\n\n"
                + ("This file has enough words but no audience or medium strategy. " * 80)
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("brand_context/personal-brand.md", message)
            self.assertIn("Audience", message)
            self.assertIn("Medium Strategy", message)

    def test_too_few_voice_samples_are_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            voice_samples = workspace_dir / "brand_context" / "voice-samples.md"
            voice_samples.write_text(
                "# Voice Samples\n\n"
                "## Status\n\n- Source status: generated_from_intake\n- Confidence: medium\n\n"
                "## Sample: Caption\n\n"
                "Text: \"Two minutes. That is the whole workout. Ready?\"\n\n"
                "- Why it matters: It shows the concise encouragement mode.\n"
                "- Voice signal: Calm, practical, second person.\n"
                "- Content mode: caption\n"
                "- Source: source_luna_fit_breakdown_001\n"
                "- Confidence: low\n"
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("voice sample", str(ctx.exception))

    def test_missing_source_intake_provenance_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            rewrite_json(
                workspace_dir / "creator-workspace.json",
                lambda manifest: manifest.update(source_intakes=[]),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("source intake", str(ctx.exception))

    def test_missing_required_asset_kind_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def drop_outfit_and_brand(library):
                library["assets"] = [
                    asset
                    for asset in library["assets"]
                    if asset["asset_type"] not in {"outfit", "brand"}
                ]

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", drop_outfit_and_brand
            )
            def remove_dropped_authorizations(plan):
                authorization = plan["setup_reference_generation"]
                authorization["asset_ids"] = [
                    asset_id
                    for asset_id in authorization["asset_ids"]
                    if asset_id not in {
                        "asset_luna_everyday_outfit",
                        "asset_luna_brand_system",
                    }
                ]
                authorization["max_calls"] = len(authorization["asset_ids"])

            rewrite_json(
                workspace_dir / "references" / "visual-continuity-plan.json",
                remove_dropped_authorizations,
            )
            remove_prompt_file(
                workspace_dir, "references/outfits/luna-everyday-outfit.prompt.md"
            )
            remove_prompt_file(
                workspace_dir, "references/brand/luna-brand-system.prompt.md"
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("outfit", str(ctx.exception))
            self.assertIn("brand", str(ctx.exception))

    def test_one_error_reports_every_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            (workspace_dir / "brand_context" / "identity.md").write_text("# Identity\n\n")
            soul = workspace_dir / "brand_context" / "soul.md"
            soul.write_text(soul.read_text() + "\nTriggers: TBD\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("brand_context/identity.md", message)
            self.assertIn("brand_context/soul.md", message)


class AssetLifecycleExistenceTests(unittest.TestCase):
    def test_approved_asset_with_missing_path_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            (workspace_dir / "references" / "video-style" / "default-video-photo-style.md").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("default-video-photo-style.md", str(ctx.exception))

    def test_prompted_asset_without_prompt_path_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def strip_outfit_prompt(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset.pop("prompt_path", None)

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", strip_outfit_prompt
            )
            remove_prompt_file(
                workspace_dir, "references/outfits/luna-everyday-outfit.prompt.md"
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("prompt_path", str(ctx.exception))

    def test_planned_asset_without_prompt_path_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def plan_outfit(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset["asset_status"] = "planned"
                        asset.pop("prompt_path", None)

            rewrite_json(workspace_dir / "references" / "reference-library.json", plan_outfit)
            remove_prompt_file(
                workspace_dir, "references/outfits/luna-everyday-outfit.prompt.md"
            )
            rebuild_brand_board(workspace_dir)

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_retired_asset_with_dead_path_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def add_retired(library):
                library["assets"].append(
                    {
                        "asset_id": "asset_luna_retired_poster",
                        "asset_type": "brand",
                        "asset_status": "retired",
                        "role": "Retired launch poster",
                        "path": "references/brand/retired-launch-poster.png",
                        "source": {"source_type": "generated", "source_ref": "old run"},
                        "created_on": "2026-06-01",
                        "usage_notes": "Do not use for new work.",
                        "semantic_index_allowed": False,
                    }
                )

            rewrite_json(workspace_dir / "references" / "reference-library.json", add_retired)
            rebuild_brand_board(workspace_dir)

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_symlinked_asset_path_escaping_the_workspace_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            outside = Path(temp_dir) / "outside-style.md"
            outside.write_text("# Outside\n")
            style_path = workspace_dir / "references" / "video-style" / "default-video-photo-style.md"
            style_path.unlink()
            style_path.symlink_to(outside)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("default-video-photo-style.md", str(ctx.exception))


class FoundationReadinessTests(unittest.TestCase):
    def test_video_foundation_ready_requires_elevenlabs_voice_design_prompt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def remove_voice_design_prompt(library):
                library["assets"] = [
                    asset
                    for asset in library["assets"]
                    if asset["asset_id"] != "asset_luna_elevenlabs_voice_design"
                ]

            rewrite_json(
                workspace_dir / "references" / "reference-library.json",
                remove_voice_design_prompt,
            )
            remove_prompt_file(
                workspace_dir,
                "references/voice/luna-fit-elevenlabs-voice-design.prompt.md",
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("ElevenLabs Voice Design prompt", str(ctx.exception))

    def test_generic_voice_note_does_not_satisfy_video_voice_design_requirement(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def replace_voice_design_with_generic_note(library):
                library["assets"] = [
                    asset
                    for asset in library["assets"]
                    if asset["asset_id"] != "asset_luna_elevenlabs_voice_design"
                ]
                library["assets"].append(
                    {
                        "asset_id": "asset_luna_voice_note",
                        "asset_type": "voice",
                        "asset_status": "prompted",
                        "role": "Generic voice note",
                        "path": "references/voice/luna-voice-note.prompt.md",
                        "prompt_path": "references/voice/luna-voice-note.prompt.md",
                        "source": {
                            "source_type": "derived",
                            "source_ref": "brand_context/voice-samples.md",
                        },
                        "created_on": "2026-06-29",
                        "usage_notes": "Generic synthetic voice note.",
                        "semantic_index_allowed": True,
                    }
                )

            rewrite_json(
                workspace_dir / "references" / "reference-library.json",
                replace_voice_design_with_generic_note,
            )
            remove_prompt_file(
                workspace_dir,
                "references/voice/luna-fit-elevenlabs-voice-design.prompt.md",
            )
            place_asset_files(workspace_dir)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("ElevenLabs Voice Design prompt", str(ctx.exception))

    def test_planned_required_kind_blocks_media_ready_generation_permission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            write_readiness_milestones(workspace_dir, foundation_mode="media_ready")

            def plan_outfit(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset["asset_status"] = "planned"
                        asset.pop("prompt_path", None)

            rewrite_json(workspace_dir / "references" / "reference-library.json", plan_outfit)
            remove_prompt_file(
                workspace_dir, "references/outfits/luna-everyday-outfit.prompt.md"
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("outfit", str(ctx.exception))

    def test_foundation_ready_prompt_ready_workspace_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


class TextFirstCreatorTests(unittest.TestCase):
    def test_active_text_first_creator_validates_with_only_universal_visual_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def make_text_first(profile):
                profile["content_strategy"]["content_mediums"] = ["text"]
                profile["reference_refs"]["primary_character_asset_ids"] = []
                profile["reference_refs"]["primary_location_asset_ids"] = []
                profile["reference_refs"].pop("primary_video_style_asset_id", None)

            rewrite_json(workspace_dir / "creator-profile.json", make_text_first)

            def strip_visual_assets(library):
                library["assets"] = [
                    {
                        "asset_id": "asset_luna_profile_mark",
                        "asset_type": "brand",
                        "asset_status": "prompted",
                        "role": "Text-first social profile mark",
                        "path": "references/brand/luna-profile-mark.png",
                        "prompt_path": "references/brand/luna-profile-mark.prompt.md",
                        "source": {
                            "source_type": "derived",
                            "source_ref": "brand_context/personal-brand.md",
                        },
                        "created_on": "2026-06-29",
                        "usage_notes": "Universal profile avatar for a text-first creator.",
                        "semantic_index_allowed": False,
                    },
                    {
                        "asset_id": "asset_luna_voice_note",
                        "asset_type": "voice",
                        "asset_status": "user_provided",
                        "role": "Author voice and cadence note",
                        "path": "references/voice/luna-voice-note.md",
                        "source": {
                            "source_type": "user_provided",
                            "source_ref": "sources/intakes/luna-fit-breakdown.md",
                        },
                        "created_on": "2026-06-29",
                        "usage_notes": "Keeps written voice consistent for text-first posts.",
                        "semantic_index_allowed": True,
                    }
                ]

            rewrite_json(workspace_dir / "references" / "reference-library.json", strip_visual_assets)
            rewrite_json(
                workspace_dir / "references" / "visual-continuity-plan.json",
                lambda plan: (
                    plan.update(
                        candidates=[],
                        selection_review={
                            "status": "draft",
                            "presented_on": None,
                            "decided_on": None,
                            "decided_by": None,
                            "terminal_review_record_id": None,
                            "notes": "No reusable visual continuity candidates are in scope.",
                        },
                    ),
                    revoke_setup_reference_generation(plan),
                ),
            )
            for prompt_path in (workspace_dir / "references").rglob("*.prompt.md"):
                prompt_path.unlink()
            voice_note = workspace_dir / "references" / "voice" / "luna-voice-note.md"
            voice_note.parent.mkdir(parents=True, exist_ok=True)
            voice_note.write_text("Calm, encouraging, second person.\n")
            profile_prompt = workspace_dir / "references" / "brand" / "luna-profile-mark.prompt.md"
            profile_prompt.write_text("Create a simple text-first profile mark.\n")

            def make_text_first_board(spec):
                spec["hero_image"] = ""
                spec["avatar_asset_id"] = "asset_luna_profile_mark"
                spec["production_spaces"] = []
                spec["signature_props"] = []

            rewrite_json(
                workspace_dir / "references" / "brand" / "personal-brand-board.json",
                make_text_first_board,
            )
            rebuild_brand_board(workspace_dir)

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


class ReferenceRefResolutionTests(unittest.TestCase):
    def test_dangling_primary_asset_id_fails_even_at_draft(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["reference_refs"]["primary_character_asset_ids"].append(
                    "asset_luna_missing_prop"
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("asset_luna_missing_prop", str(ctx.exception))

    def test_primary_ref_type_mismatch_fails_even_at_draft(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["reference_refs"].update(
                    primary_video_style_asset_id="asset_luna_brand_system"
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("asset_luna_brand_system", message)
            self.assertIn("video_style", message)

    def test_empty_primary_refs_for_video_creator_are_blockers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def empty_primaries(profile):
                profile["reference_refs"]["primary_character_asset_ids"] = []
                profile["reference_refs"]["primary_location_asset_ids"] = []

            rewrite_json(workspace_dir / "creator-profile.json", empty_primaries)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("primary_character_asset_ids", message)
            self.assertIn("primary_location_asset_ids", message)

    def test_missing_video_style_primary_for_video_creator_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["reference_refs"].pop("primary_video_style_asset_id"),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("primary_video_style_asset_id", str(ctx.exception))

    def test_retired_primary_ref_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def retire_primary_keep_kind(library):
                for asset in library["assets"]:
                    if asset["asset_id"] == "asset_luna_identity_plate":
                        asset["asset_status"] = "retired"
                library["assets"].append(
                    {
                        "asset_id": "asset_luna_identity_plate_v2",
                        "asset_type": "character",
                        "asset_status": "prompted",
                        "role": "Replacement identity plate",
                        "path": "references/character/luna-identity-plate-v2.png",
                        "prompt_path": "references/character/luna-identity-plate-v2.prompt.md",
                        "source": {
                            "source_type": "derived",
                            "source_ref": "sources/intakes/luna-fit-breakdown.md",
                        },
                        "created_on": "2026-07-03",
                        "usage_notes": "Replacement in progress.",
                        "semantic_index_allowed": False,
                    }
                )

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", retire_primary_keep_kind
            )
            prompt = workspace_dir / "references" / "character" / "luna-identity-plate-v2.prompt.md"
            prompt.write_text("prompt\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("retired", str(ctx.exception))
            self.assertIn("asset_luna_identity_plate", str(ctx.exception))

    def test_foundation_ready_requires_prompted_primary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def plan_primary_keep_kind(library):
                for asset in library["assets"]:
                    if asset["asset_id"] == "asset_luna_identity_plate":
                        asset["asset_status"] = "planned"
                        asset.pop("prompt_path", None)
                library["assets"].append(
                    {
                        "asset_id": "asset_luna_identity_plate_v2",
                        "asset_type": "character",
                        "asset_status": "prompted",
                        "role": "Prompted identity plate",
                        "path": "references/character/luna-identity-plate-v2.png",
                        "prompt_path": "references/character/luna-identity-plate-v2.prompt.md",
                        "source": {
                            "source_type": "derived",
                            "source_ref": "sources/intakes/luna-fit-breakdown.md",
                        },
                        "created_on": "2026-07-03",
                        "usage_notes": "Prompted replacement.",
                        "semantic_index_allowed": False,
                    }
                )

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", plan_primary_keep_kind
            )
            prompt = workspace_dir / "references" / "character" / "luna-identity-plate-v2.prompt.md"
            prompt.write_text("prompt\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("asset_luna_identity_plate", message)
            self.assertIn("prompted or later", message)


class AssetSourceRefTests(unittest.TestCase):
    def test_dangling_or_escaping_source_ref_is_a_blocker(self):
        for bad_ref in ("sources/intakes/does-not-exist.md", "../../outside.md", "old run"):
            with tempfile.TemporaryDirectory() as temp_dir:
                workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

                def corrupt_source_ref(library, ref=bad_ref):
                    for asset in library["assets"]:
                        if asset["asset_type"] == "outfit":
                            asset["source"]["source_ref"] = ref

                rewrite_json(
                    workspace_dir / "references" / "reference-library.json", corrupt_source_ref
                )

                with self.subTest(source_ref=bad_ref):
                    with self.assertRaises(ValidationError) as ctx:
                        validate_creator_workspace(workspace_dir)
                    self.assertIn("source_ref", str(ctx.exception))

    def test_recorded_intake_id_source_ref_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")

            def intake_id_source_ref(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset["source"]["source_ref"] = "source_luna_fit_breakdown_001"

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", intake_id_source_ref
            )
            rebuild_brand_board(workspace_dir)

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


if __name__ == "__main__":
    unittest.main()
