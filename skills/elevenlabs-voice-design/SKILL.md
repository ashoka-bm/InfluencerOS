---
name: elevenlabs-voice-design
description: Use when staging an ElevenLabs Voice Design prompt package for creator voice continuity; never generate, upload, or approve audio.
---

# ElevenLabs Voice Design

Stage an ElevenLabs Voice Design prompt package for a creator reference asset.
The output is a prompt file humans can copy into ElevenLabs. Do not call
ElevenLabs, create a voice, generate audio, upload files, or imply provider
approval.

## Inputs

Read the creator workspace sources needed to fill the voice fields:

- `creator-profile.json`
- `brand_context/identity.md`
- `brand_context/soul.md`
- `brand_context/personal-brand.md`
- `brand_context/voice-samples.md`
- `references/reference-library.json`, when present

If the user provides a narrower brief, use it and mark unknown fields as
`unspecified`; do not invent ethnicity, regional upbringing, or diaspora
context when the source materials do not support them.

## Workflow

1. **Extract voice identity fields.** Build the fields before drafting the
   prompt. Always include:
   - Language
   - Ethnicity / cultural background
   - Regional upbringing
   - Diaspora context
   - Gender
   - Perceived age range
   - Persona
   - Emotion
   - Timbre / pitch
   - Pacing
   - Accent / cadence
   - Pronunciation notes
   - Avoid

   Completion: every field is present; unknown fields are marked
   `unspecified`, not silently omitted.

2. **Represent cultural identity carefully.** Use ethnicity and cultural
   background as grounded context, not caricature. Use `accent` only for a
   regional dialect or sound. Use `cadence`, `intonation`, `delivery`, or
   `rhythm` for speech pattern.

   Prefer:
   - `African American woman from Brooklyn with educated African American cadence`
   - `Ghanaian American woman with African American family-register warmth and light West African familial influence`
   - `Black British professional cadence with warm Caribbean family-register softness`

   Avoid:
   - `ethnic voice`
   - `urban`
   - `exotic`
   - broad labels like `African accent` unless the brief specifies country, region, language, or dialect
   - exaggerated dialect unless the source brief explicitly asks for it

   Completion: the prompt names ethnicity/cultural background and uses precise
   register language without flattening the creator.

3. **Write the Voice Design prompt.** Use this structure:

   ```text
   Native <Language>, <dialect or regional delivery>. <Gender>, <Age range>. <Quality level>.
   Persona: <2-5 words>. Emotion: <2-3 adjectives>.
   <1-2 sentences about timbre, pacing, delivery, accent/cadence, cultural register, and avoid-list>
   ```

   Keep language and dialect distinct from cadence. Use an ElevenLabs quality
   descriptor exactly: `Excellent quality`, `Studio quality`, or `Broadcast
   quality`. Do not substitute vague wording such as `high-quality natural
   voice`.

   Completion: the prompt is paste-ready, concise, and does not include
   unrelated biography.

4. **Write preview text.** Match the preview to the creator's actual voice
   samples and content modes. Default identity-, dialect-, or cadence-heavy
   voices to `medium`; use `short` for broad/neutral voices or when the operator
   explicitly prioritizes generation cost:
   - `short`: 50-90 words
   - `medium`: 100-160 words
   - `long`: 170-260 words

   Use performance cues sparingly:
   - `[soft breath]`
   - `[small laugh]`
   - `[dry laugh]`
   - `[exhales]`
   - `[pause]`
   - `[warmer]`
   - `[firm, calm]`

   Completion: the preview demonstrates cadence, pacing, emotion, and cultural
   register without becoming theatrical.

5. **Recommend guidance and iteration notes.** Emit one starting value, plus an
   optional iteration range:
   - Start at `30%` (`25%-35%` iteration range) when naturalness matters more
     than exact identity traits.
   - Start at `40%` (`35%-45%` iteration range) when dialect, cadence, or persona
     accuracy matters.
   - Higher only when the user explicitly prioritizes strict adherence over
     audio quality.

   Add one or two notes about what to change if the generated preview sounds too
   regional, too generic, too theatrical, or too corporate.

6. **Emit the prompt-file body.** Create content suitable for:

   ```text
   references/voice/<asset-slug>.prompt.md
   ```

   Completion: the file body includes the output shape below and explicitly
   states that a human must copy the prompt into ElevenLabs and bring any
   resulting sample back through the asset import/provider boundary.

## Output Shape

```text
# <Creator Name> ElevenLabs Voice Design Prompt

Status: prompted
Provider boundary: Draft only. Human must copy this into ElevenLabs; no audio generation is approved by this file.
Reference asset id: <asset_id>
Source refs:
- <path>

## Voice Identity Fields

- Language:
- Ethnicity / cultural background:
- Regional upbringing:
- Diaspora context:
- Gender:
- Age range:
- Persona:
- Emotion:
- Timbre / pitch:
- Pacing:
- Accent / cadence:
- Pronunciation notes:
- Avoid:

## Voice Design Prompt

<paste-ready ElevenLabs Voice Design prompt>

## Preview Text

<paste-ready preview script>

## Guidance Scale

Recommended starting value: <integer>%.
Iteration range: <low>%-<high>%.
<one-sentence rationale>

## Human-In-The-Loop Instructions

1. Copy the Voice Design Prompt and Preview Text into ElevenLabs.
2. Generate voice options manually.
3. Select a candidate only if it matches the identity fields and avoid-list.
4. Register a separate voice-sample asset with an audio path and `prompt_path` pointing back to this prompt asset.
5. Bring the exported voice sample into that separate asset through the approved import/provider-boundary path.

## Iteration Notes

- <one or two tuning notes>
```

## Reference Library Entry

When this skill stages a prompt file, `create-reference-library` should add or
update a `references/reference-library.json` asset like:

```json
{
  "asset_id": "asset_<slug>_elevenlabs_voice_design",
  "asset_type": "voice",
  "asset_status": "prompted",
  "role": "ElevenLabs Voice Design prompt for synthetic spoken voice continuity",
  "path": "references/voice/<slug>-elevenlabs-voice-design.prompt.md",
  "prompt_path": "references/voice/<slug>-elevenlabs-voice-design.prompt.md",
  "source": {
    "source_type": "derived",
    "source_ref": "brand_context/voice-samples.md"
  },
  "created_on": "YYYY-MM-DD",
  "usage_notes": "Use as the human-in-the-loop prompt package for manual ElevenLabs Voice Design. This is not generated audio and does not approve provider calls.",
  "semantic_index_allowed": true
}
```

The prompt asset remains `prompted`. Never import generated or approved audio
into its `.prompt.md` path.

## Approved Voice Sample Entry

Before importing a selected preview, add a separate Reference Library asset:

```json
{
  "asset_id": "asset_<slug>_approved_voice_preview",
  "asset_type": "voice",
  "asset_status": "planned",
  "role": "Approved voice preview for synthetic spoken voice continuity",
  "path": "references/voice/<slug>-approved-voice-preview.mp3",
  "prompt_path": "references/voice/<slug>-elevenlabs-voice-design.prompt.md",
  "source": {
    "source_type": "derived",
    "source_ref": "references/voice/<slug>-elevenlabs-voice-design.prompt.md"
  },
  "created_on": "YYYY-MM-DD",
  "usage_notes": "Import the human-selected preview here, then mark it approved only after explicit human approval.",
  "semantic_index_allowed": false
}
```

Importing updates the sample asset's provenance and lifecycle. Explicit human
approval may then advance the sample to `approved`; it never changes the prompt
asset's status or bytes.

## References

Read `references/examples.md` when the user wants variants, a shorter preview,
or help tuning a prompt that sounded wrong after manual ElevenLabs testing.
