# Standard Outfit Reference Prompts

Use these when you have a person reference image and a separate outfit or garment reference image. The person image controls identity. The outfit image controls wardrobe only.

## Reference Scope

- `@person_reference`: controls face, age, body type, skin texture, hair, expression baseline, and identity.
- `@outfit_reference`: controls outfit silhouette, cut, fabric, construction, colorway, styling, footwear, and accessories.
- Optional `@video_style_reference`: controls camera source, aspect ratio, framing, lighting, movement, and shot quality only for scene placement prompts.
- Do not transfer the outfit model's face, body, pose, background, lighting, or camera angle.
- Keep the generated person recognizable as the person in `@person_reference`.

## Character Wearing Outfit

```text
Create a realistic full-body fashion reference image of the person from @person_reference wearing the outfit from @outfit_reference.

Identity: Preserve the face, age, body type, skin texture, hair, expression baseline, and natural proportions from @person_reference.

Wardrobe: Transfer only the outfit from @outfit_reference: silhouette, cut, fabric, construction, colorway, fit, layering, footwear, and accessories. Do not transfer the outfit model's face, body, pose, background, lighting, or camera angle.

Presentation: Full body visible head to feet, neutral standing pose, clean studio lighting, flat matte neutral gray background. Show the outfit clearly enough for future image and video continuity.

Continuity details: Preserve garment seams, buttons, lapels, cuffs, hem length, trouser or skirt shape, shoe design, jewelry, bag, and any signature styling details. Keep styling polished and natural.

Avoid: identity drift, face swap artifacts, changing the person's age, changing body proportions, extra people, extra garments, visible text, logos unless approved, watermarks, busy background, distorted hands or feet.
```

## Four-View Wardrobe Sheet

```text
Create a character wardrobe reference sheet for the person from @person_reference wearing the outfit from @outfit_reference.

Show four views on a flat matte neutral gray background:

1. Full-body front three-quarter view, head to feet visible.
2. Full-body rear view, head to feet visible.
3. Upper-body wardrobe detail, showing face identity plus neckline, jacket, top, jewelry, fabric texture, and styling.
4. Lower-body wardrobe detail, showing waist, seams, hem, footwear, fabric drape, and accessories.

Identity: Preserve the same person from @person_reference across every view.

Wardrobe: Use @outfit_reference only for clothing, fit, fabric, color, footwear, and accessories. Do not copy the outfit reference model's face, body, pose, location, or lighting.

Presentation: Clean studio lighting, consistent proportions, no visible labels, no watermark, no extra people, no environment.
```

## Scene Placement With Outfit

```text
Place the person from @person_reference into the requested scene while wearing the outfit from @outfit_reference.

Subject: Same person as @person_reference. Preserve identity, age, hair, skin texture, body type, and expression style.

Wardrobe: Same outfit as @outfit_reference. Preserve silhouette, fabric, color, fit, footwear, and accessories. The outfit reference controls wardrobe only.

Scene: [DESCRIBE LOCATION, MOOD, ACTION, CAMERA ANGLE, LIGHTING, AND ASPECT RATIO]. If @video_style_reference is attached, use it for camera source, framing, lighting, movement feel, platform format, and shot quality.

Composition: Make the person look naturally present in the scene. Match perspective, scale, contact shadows, lighting direction, and depth of field.

Avoid: changing identity, copying the outfit reference model, adding extra people, changing the outfit color or cut, warped hands, warped shoes, visible text, watermarks, over-stylized skin, artificial fashion-catalog stiffness.
```
