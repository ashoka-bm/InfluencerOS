# Examples

Use these as patterns, not fixed templates. Preserve the source brief's
identity, register, boundaries, and voice samples.

## African American Creator Voice

```text
# Adira Mensah-Yates ElevenLabs Voice Design Prompt

Status: prompted
Provider boundary: Draft only. Human must copy this into ElevenLabs; no audio generation is approved by this file.
Reference asset id: asset_adira_elevenlabs_voice_design
Source refs:
- brand_context/identity.md
- brand_context/soul.md
- brand_context/personal-brand.md
- brand_context/voice-samples.md

## Voice Identity Fields

- Language: Native English
- Ethnicity / cultural background: African American and Ghanaian American
- Regional upbringing: Brooklyn, New York, with Macon family roots and Kumasi family context
- Diaspora context: Transatlantic Black diasporic creator across US, UK, and Ghana
- Gender: Female
- Age range: 34-38
- Persona: disciplined mentor
- Emotion: warm, composed, authoritative
- Timbre / pitch: smooth, grounded, mid-low
- Pacing: measured and patient
- Accent / cadence: educated African American cadence with subtle Brooklyn warmth and light transatlantic professional intonation
- Pronunciation notes: preserve Ghanaian names and place names carefully
- Avoid: generic corporate narrator, exaggerated dialect, salesy delivery, bubbly influencer tone

## Voice Design Prompt

Native English, African American and Ghanaian American woman from Brooklyn with educated African American cadence, subtle New York warmth, and light transatlantic professional intonation. Female, 34-38. Excellent quality.
Persona: disciplined mentor. Emotion: warm, composed, authoritative.
A smooth, grounded, mid-low female voice with natural texture, calm confidence, and a caring teacher's presence. Her delivery carries African American family-register warmth while staying precise, professional, and measured; never salesy, bubbly, theatrical, or generically corporate.

## Preview Text

[soft breath]
Two ledgers. Two languages. Same discipline.
[small laugh] Y'all know I am not romanticizing struggle. Poverty is not character development. We are not doing that.
But writing the number down gave both families power.
[dry laugh] The seven-dollar latte is not the enemy. The seven-hundred-dollar housing decision is the lever.
My grandmother called it keeping your business straight.
Same lesson. Different language.
[firm, calm]
Discipline can be inherited, practiced, and taught.
That is the work.

## Guidance Scale

40% — keep cadence and persona specific while preserving natural audio quality.

## Iteration Notes

- If it sounds too British, remove `light transatlantic professional intonation`.
- If it sounds too generic, strengthen `African American family-register warmth`.
```

## Cost-Aware Preview Trimming

When the preview is too expensive, reduce in this order:

1. Remove repeated examples.
2. Keep one performance cue at the start and one emotional direction near the end.
3. Preserve the line that best demonstrates cultural register.
4. Preserve one sentence with the target pacing.
5. Preserve one strong close.

Before:

```text
[soft breath]
Two ledgers. Two languages. Same discipline.
[small laugh] Y'all know I am not romanticizing struggle. Poverty is not character development. We are not doing that.
But writing the number down gave both families power.
[dry laugh] The seven-dollar latte is not the enemy. The seven-hundred-dollar housing decision is the lever.
My grandmother called it keeping your business straight.
Same lesson. Different language.
[firm, calm]
Discipline can be inherited, practiced, and taught.
That is the work.
```

After:

```text
[small laugh] Y'all know I am not romanticizing struggle. We are not doing that.
But writing the number down gave both families power.
The seven-dollar latte is not the enemy. The seven-hundred-dollar housing decision is the lever.
[firm, calm]
Discipline can be inherited, practiced, and taught.
That is the work.
```
