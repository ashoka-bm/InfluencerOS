# Standard Character Object Prompts

Use these when you have a person reference image and a separate object, product, or prop reference image. The person image controls identity. The object image controls the prop only.

## Reference Scope

- `@person_reference`: controls face, age, body type, hair, skin texture, and identity.
- `@object_reference`: controls the object's shape, material, color, scale, markings, hardware, and construction.
- Optional `@wardrobe_reference`: controls clothing only.
- Optional `@location_reference`: controls setting only.
- Optional `@video_style_reference`: controls camera source, aspect ratio, framing, lighting, movement, and shot quality only for lifestyle or character-use prompts.
- Do not transfer hands, people, background, lighting, or camera angle from the object reference unless requested.

## Object Multi-Angle Reference Sheet

```text
Create one object reference sheet divided into clean sections for the same object from @object_reference, on a flat matte neutral gray background.

SECTION 1 - FRONT / IDENTITY VIEW
Show the full object from the front or front three-quarter angle. Preserve shape, color, material, proportions, scale cues, and identity-bearing marks.

SECTION 2 - SIDE / DEPTH VIEW
Show the full side or profile view. Preserve thickness, silhouette, handles, ports, hinges, legs, seams, strap, clasp, or other depth-critical details.

SECTION 3 - REAR / BACK VIEW
Show the rear view. Preserve back construction, surface wear, material transitions, markings, controls, vents, cables, clasp, buckle, or approved logos.

SECTION 4 - MACRO DETAIL
Show close-up details: material grain, glass, buttons, cracks, seams, wear, labels, hardware, stitching, chain links, stones, texture, or transformation marks.

Presentation: Clean studio lighting, consistent object identity, no extra objects, no hands unless scale or handling is explicitly required, no environment, no visible text unless approved, no watermark.
```

## Character Holding Or Wearing Object

```text
Create a realistic image of the person from @person_reference with the object from @object_reference.

Identity: Preserve the face, age, hair, skin texture, body type, and expression style from @person_reference.

Object: Preserve the shape, material, color, scale, construction, markings, and distinctive details from @object_reference. The object reference controls the prop only.

Interaction: [DESCRIBE HOW THE PERSON HOLDS, WEARS, USES, OPENS, POINTS TO, CARRIES, OR DISPLAYS THE OBJECT].

Wardrobe: [DESCRIBE OUTFIT] or use @wardrobe_reference if attached. If @wardrobe_reference is attached, it controls clothing only.

Location: [DESCRIBE LOCATION] or use @location_reference if attached. If @location_reference is attached, it controls setting only.

Camera and lighting: [DESCRIBE CAMERA, LIGHTING, AND ASPECT RATIO] or use @video_style_reference if attached. If @video_style_reference is attached, it controls camera source, framing, lighting, movement feel, platform format, and shot quality only.

Integration: Match hand contact, grip, shadows, reflections, scale, and perspective. The object should feel physically present and correctly sized.

Avoid: identity drift, object duplication, changing object design, unreadable or fake logos unless approved, fused fingers, impossible grip, floating object, extra people, visible text, watermarks.
```

## Product Or Prop Lifestyle Still

```text
Create a polished lifestyle still featuring the person from @person_reference and the object from @object_reference.

Subject role: The person remains recognizable and natural. Preserve identity from @person_reference.

Object role: The object remains accurate and inspectable. Preserve form, materials, color, scale, and important details from @object_reference.

Scene: [DESCRIBE WHERE THIS HAPPENS].

Action: [DESCRIBE WHAT THE PERSON IS DOING WITH THE OBJECT].

Camera: [DESCRIBE SHOT SIZE, ANGLE, LENS FEEL, AND ASPECT RATIO]. If @video_style_reference is attached, use it for camera source, framing, lighting, movement feel, platform format, and shot quality.

Mood: [DESCRIBE EMOTIONAL OR BRAND TONE].

Avoid: turning the object into a different product, adding duplicate objects, over-branding, changing the person's face, mismatched lighting, fake text, extra people, watermarks.
```
