import json
import tempfile
import unittest
from pathlib import Path

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
    (workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md").write_text(
        (ROOT / "examples" / "sources" / "luna-fit-breakdown.example.md").read_text()
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


def make_ready_workspace(temp_dir, status):
    workspace_dir = init_workspace_with_status(temp_dir, status)
    populate_foundation(workspace_dir)
    place_asset_files(workspace_dir)
    return workspace_dir


class DraftLenienceTests(unittest.TestCase):
    def test_draft_workspace_with_scaffold_foundation_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


class ReferenceLibraryIntegrityTests(unittest.TestCase):
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


class ContentReadyBlockerTests(unittest.TestCase):
    def test_populated_content_ready_workspace_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_scaffold_only_foundation_file_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            identity = workspace_dir / "brand_context" / "identity.md"
            identity.write_text("# Identity\n\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("brand_context/identity.md", str(ctx.exception))

    def test_tbd_placeholder_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            soul = workspace_dir / "brand_context" / "soul.md"
            soul.write_text(soul.read_text() + "\nHumor rules: TBD\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("TBD", str(ctx.exception))

    def test_oversized_context_file_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            soul = workspace_dir / "context" / "SOUL.md"
            soul.write_text(soul.read_text() + ("Luna keeps sessions tiny. " * 200))

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("context/SOUL.md", str(ctx.exception))
            self.assertIn("byte cap", str(ctx.exception))

    def test_sentence_stub_foundation_file_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
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
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
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
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
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
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            rewrite_json(
                workspace_dir / "creator-workspace.json",
                lambda manifest: manifest.update(source_intakes=[]),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("source intake", str(ctx.exception))

    def test_missing_required_asset_kind_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            def drop_outfit_and_brand(library):
                library["assets"] = [
                    asset
                    for asset in library["assets"]
                    if asset["asset_type"] not in {"outfit", "brand"}
                ]

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", drop_outfit_and_brand
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("outfit", str(ctx.exception))
            self.assertIn("brand", str(ctx.exception))

    def test_one_error_reports_every_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
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
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            (workspace_dir / "references" / "video-style" / "default-video-photo-style.md").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("default-video-photo-style.md", str(ctx.exception))

    def test_prompted_asset_without_prompt_path_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            def strip_outfit_prompt(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset.pop("prompt_path", None)

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", strip_outfit_prompt
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("prompt_path", str(ctx.exception))

    def test_planned_asset_without_prompt_path_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            def plan_outfit(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset["asset_status"] = "planned"
                        asset.pop("prompt_path", None)

            rewrite_json(workspace_dir / "references" / "reference-library.json", plan_outfit)

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_retired_asset_with_dead_path_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

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

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_symlinked_asset_path_escaping_the_workspace_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            outside = Path(temp_dir) / "outside-style.md"
            outside.write_text("# Outside\n")
            style_path = workspace_dir / "references" / "video-style" / "default-video-photo-style.md"
            style_path.unlink()
            style_path.symlink_to(outside)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("default-video-photo-style.md", str(ctx.exception))


class GenerationReadyTests(unittest.TestCase):
    def test_planned_required_kind_blocks_generation_ready(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "generation_ready")

            def plan_outfit(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset["asset_status"] = "planned"
                        asset.pop("prompt_path", None)

            rewrite_json(workspace_dir / "references" / "reference-library.json", plan_outfit)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("outfit", str(ctx.exception))

    def test_fully_prompted_generation_ready_workspace_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "generation_ready")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


class TextFirstCreatorTests(unittest.TestCase):
    def test_active_text_first_creator_validates_without_visual_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "active")

            def make_text_first(profile):
                profile["content_strategy"]["content_mediums"] = ["text"]
                profile["reference_refs"]["primary_character_asset_ids"] = []
                profile["reference_refs"]["primary_location_asset_ids"] = []
                profile["reference_refs"].pop("primary_video_style_asset_id", None)

            rewrite_json(workspace_dir / "creator-profile.json", make_text_first)

            def strip_visual_assets(library):
                library["assets"] = [
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
            voice_note = workspace_dir / "references" / "voice" / "luna-voice-note.md"
            voice_note.parent.mkdir(parents=True, exist_ok=True)
            voice_note.write_text("Calm, encouraging, second person.\n")

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
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

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
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["reference_refs"].pop("primary_video_style_asset_id"),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("primary_video_style_asset_id", str(ctx.exception))

    def test_retired_primary_ref_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

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

    def test_generation_ready_requires_prompted_primary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "generation_ready")

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
                workspace_dir = make_ready_workspace(temp_dir, "content_ready")

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
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            def intake_id_source_ref(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset["source"]["source_ref"] = "source_luna_fit_breakdown_001"

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", intake_id_source_ref
            )

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


if __name__ == "__main__":
    unittest.main()
