# Standard Character Asset Prompts

Use these to create reusable identity assets from one or more person reference images. These assets become the anchor for later outfits, locations, props, stills, and video prompts.

## Reference Scope

- `@person_reference`: controls identity, face, age, skin texture, hair, body type, proportions, and expression baseline.
- Optional `@style_reference`: controls visual style only.
- Optional `@wardrobe_reference`: controls clothing only.
- Do not transfer background, lighting, camera angle, or other people from any reference unless explicitly requested.
- Do not apply `@video_style_reference`, creator location style, or brand aesthetic to the first three identity-locking character assets. These assets must stay neutral and environment-free.

## Non-Negotiable Character Asset Rules

Identity plate, full-body turnaround sheet, and macro detail card must use:

- flat matte neutral gray background;
- clean studio lighting;
- no environment;
- no lifestyle room;
- no location texture;
- no props unless explicitly required for identity continuity;
- no visible text;
- no watermark.

If the output uses a home, kitchen, studio apartment, gym, outdoor scene, branded backdrop, warm lifestyle setting, or any non-gray environment, it is a failed character-reference generation and should not be marked `approved`.

## Character Identity Plate

```text
Create a dead-on character identity plate of the person from @person_reference.

Subject: Preserve the person's face structure, age, skin texture, hair color, hairstyle, eye shape, mouth, jawline, natural marks, and expression baseline.

Pose and framing: Straight-on portrait or upper-body identity image. Neutral calm expression. Shoulders relaxed. Face clearly visible and evenly lit.

Presentation: Clean studio lighting, flat matte neutral gray background, realistic skin texture, no beauty over-smoothing, no environment, no lifestyle background, no props, no extra figures, no visible text, no watermark.

Purpose: This image should lock identity for future close-ups, outfit changes, location scenes, and video prompts.
```

## Full-Body Turnaround Sheet

```text
Create a full-body character turnaround sheet for the person from @person_reference.

Show the same person in four consistent views on a flat matte neutral gray background:

1. Full-body front view.
2. Full-body side view.
3. Full-body rear view.
4. Full-body three-quarter view.

Identity: Preserve face, age, hair, body type, proportions, posture baseline, and natural presence from @person_reference.

Wardrobe: Use [DESCRIBE BASE OUTFIT] or use @wardrobe_reference if attached. Keep clothing simple enough to reveal silhouette and proportions.

Presentation: Full body visible head to feet in every view, flat matte neutral gray background, clean studio lighting, consistent scale across views, no environment, no lifestyle background, no props unless approved, no visible text, no watermark.

Purpose: This sheet should lock body proportions, silhouette, stance, outfit baseline, and full-body continuity.
```

## Macro Detail Card

```text
Create a macro character detail card for the person from @person_reference.

One image divided into clean sections showing:

1. Eyes and brow detail.
2. Mouth and smile baseline.
3. Skin texture and natural marks.
4. Hair texture and hairline.
5. Hands.
6. Wardrobe fabric or signature accessory detail, if relevant.

Identity: Preserve the same person from @person_reference in every section.

Presentation: Clean studio lighting, flat matte neutral gray background or neutral gray section backgrounds, realistic texture, no environment, no lifestyle background, no extra people, no visible text unless labels are explicitly requested for human review, no watermark.

Purpose: This card should help future close-ups preserve the person's small identity details.
```

## Three-Asset Character Package

```text
Create three separate character reference images for the same person from @person_reference. All three images must use a flat matte neutral gray background, clean studio lighting, no environment, no lifestyle background, no props unless explicitly approved, no visible text, and no watermark.

IMAGE 1 - DEAD-ON IDENTITY PLATE
Straight-on portrait or upper-body identity plate. Preserve face structure, head shape, hair, eye shape, skin texture, age, visible marks, and expression baseline. Clean studio lighting, no environment, no text, no extra figures.

IMAGE 2 - FULL-BODY TURNAROUND SHEET
Full-body front, side, rear, and three-quarter views of the same person. Full body visible head to feet in every view. Preserve proportions, silhouette, posture baseline, base outfit, footwear, and scale. Clean studio lighting, no environment, no text, no extra figures.

IMAGE 3 - MACRO DETAIL CARD
One image divided into clean sections showing the same person's defining details: eyes, mouth, skin texture, hair texture, hands, clothing fabric, accessories, natural marks, and other continuity-critical details. Preserve the same identity and style. No environment, no text unless labels are requested for human review.
```
