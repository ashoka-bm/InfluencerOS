# Standard Video/Photo Style Prompt

Use this to create the creator's reusable `@video_style_reference`.

This reference controls production style only. It does not control identity, outfit, location layout, props, or the full shot list for a specific video.

## Prompt

Create a concise video/photo style card for this creator.

Source material:

- `brand_context/identity.md`
- `brand_context/personal-brand.md`
- `creator-profile.json`
- user-provided visual references, if any

Define:

- **Camera:** primary camera source, lens feel, image quality, stabilization, and default aspect ratio.
- **Lighting:** default light source, color temperature, contrast level, and any recurring location-specific lighting.
- **Framing:** default shot distances, camera height, crop rules, and still-image crop guidance.
- **Movement:** default motion style, handheld/tripod preference, and movement to avoid.
- **Finish:** skin texture, color grade, realism level, background feel, and retouching boundaries.
- **Recurring shot families:** only durable creator habits, such as talking head, fit check, desk tutorial, kitchen counter detail, walking vlog, product close-up, or gym side angle.

Output:

1. A short style summary.
2. The locked `@video_style_reference` text for future prompts.
3. A short list of recurring shot families, if any.
4. A boundary note naming what this style reference must not change.

Default when unspecified:

Modern phone-first vertical creator content. Use a modern iPhone-style camera, 9:16 social format, natural window light with optional soft LED or ring light, crisp phone realism, natural skin texture, tidy lived-in backgrounds, stable tripod or light handheld movement, and a believable social-native finish. Avoid cinematic drama, heavy retouching, overproduced studio lighting, fake text, watermarks, and stock-photo stiffness.
