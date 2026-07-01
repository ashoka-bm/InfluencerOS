# Standard AI Influencer Location Prompts

Use these when you have a person reference image and a separate location reference image. The person image controls identity. The location image controls the repeatable creator space: home, kitchen, bedroom, bathroom, closet, gym, office, studio, car, lobby, cafe corner, hotel room, or outdoor daily-life spot.

## Reference Scope

- `@person_reference`: controls face, age, body type, hair, skin texture, and identity.
- `@location_reference`: controls architecture, layout, furniture, equipment, decor, mirrors, windows, color palette, light, and atmosphere.
- Optional `@spatial_map_reference`: controls blocking only: where the person stands, sits, enters, exits, turns, works out, cooks, films, or moves through the space.
- Optional `@wide_anchor_reference`: controls continuity after a first wide shot has been generated. Use this for later medium shots and close-ups so furniture, equipment, decor, props, and room geography stay fixed.
- Optional `@wardrobe_reference`: controls clothing only.
- Optional `@video_style_reference`: controls camera source, aspect ratio, framing, lighting, movement, and shot quality only.
- Do not transfer people from the location reference unless requested.
- Keep enough open space for the person to stand, sit, walk, stretch, exercise, cook, dress, film, or interact naturally.
- Treat locations as reusable creator sets, not one-off cinematic backgrounds.

## Common Influencer Spaces

Use these location roles when naming or describing a new space:

- Home base: living room, kitchen, bedroom, bathroom, hallway, entryway, closet, balcony, patio.
- Fitness: home gym, commercial gym corner, pilates studio, yoga mat area, locker room mirror area.
- Work: home office, podcast corner, desk setup, studio backdrop, content filming wall.
- Lifestyle: cafe table, hotel room, car interior, lobby, wellness studio, grocery aisle, walking route.

Each recurring space should have a stable look: fixed furniture, clear camera positions, believable daily objects, and enough negative space for the influencer to move.

## Master Influencer Location Sheet

```text
Create a master location reference sheet for the same creator location from @location_reference.

Show five clean views of the same space on one sheet:

1. Wide room view that shows the full layout, entrances, exits, windows, mirrors, furniture, equipment, counters, bed, sofa, desk, or major anchors.
2. Creator filming angle: the most natural angle for a selfie, tripod, vlog, tutorial, GRWM, workout, cooking, or talking-head post.
3. Reverse angle from the opposite side, preserving the same architecture, furniture, and fixed objects.
4. Functional interaction angle showing where the person can stand, sit, stretch, cook, dress, work, hold a product, or move through the space.
5. Detail angle showing surfaces, textures, decor, equipment, storage, counters, mirror, bedding, lighting, or signature personal objects.

Continuity: Keep furniture, decor, mirrors, windows, doors, counters, equipment, plants, artwork, rugs, light direction, and fixed objects consistent across all views. Make the relationship between angles clear.

Staging: Leave natural negative space for a person and camera. The location should work for repeated posts without looking empty or staged.

Presentation: No characters, no extra people, no visible text, no watermark. This should become the central reusable location reference for stills and short videos.
```

## Daily-Life Location Variants

```text
Create controlled daily-life variants of the same creator location from @location_reference.

Keep the exact same architecture, layout, doors, windows, furniture positions, equipment, mirrors, counters, and camera geography. Change only the requested daily-life state.

STATE A - CLEAN BASE
Clean, reset version of the location. Polished but believable, not sterile.

STATE B - LIVED-IN
Same location with subtle daily use: a mug, towel, robe, notebook, skincare, gym mat, water bottle, folded clothes, grocery bag, laptop, or small personal items. Keep it tidy enough for influencer content.

STATE C - ACTIVE USE
Same location during a specific activity: cooking, workout, stretching, skincare, makeup, getting dressed, journaling, laptop work, filming setup, product use, or unpacking. Preserve the room layout.

STATE D - TIME OF DAY
Same location in morning, midday, golden hour, evening lamp light, or night practical lighting. Preserve geography and fixed anchors while changing only the light and mood.

Avoid: changing the room, moving major furniture unless requested, inventing new doors or windows, adding people, adding visible text, making the space messy beyond normal daily use, changing architectural style.
```

## Place Influencer Into Location

```text
Place the person from @person_reference naturally into the creator location from @location_reference.

Identity: Preserve the face, age, hair, skin texture, body type, and expression style from @person_reference.

Location: Preserve the architecture, layout, furniture, mirrors, counters, equipment, decor, materials, color palette, light direction, spatial anchors, and atmosphere from @location_reference. Do not invent a different room or setting.

Blocking: If @spatial_map_reference is attached, use it only for position and movement. Place the person where the map indicates. Do not copy the map's colors, shapes, labels, or low-poly style.

Continuity anchor: If @wide_anchor_reference is attached, preserve the exact geography, furniture positions, decor, props, equipment, and lighting from that wide anchor. Use it as the background truth for this closer shot.

Wardrobe: [DESCRIBE OUTFIT] or use @wardrobe_reference if attached. If @wardrobe_reference is attached, it controls clothing only.

Action: [DESCRIBE EVERYDAY ACTION: making coffee, stretching, mirror selfie, skincare, typing, walking in, packing a bag, holding a product, cooking, changing shoes, setting up a tripod].

Camera: [DESCRIBE CREATOR CAMERA STYLE: phone selfie, tripod reel, mirror shot, chest-up talking head, waist-up tutorial, full-body fit check, overhead counter shot, gym side angle, handheld vlog]. If @video_style_reference is attached, use it for camera source, aspect ratio, framing, lighting, movement feel, and shot quality.

Integration: Match perspective, scale, contact shadows, mirror logic, lighting direction, depth of field, and color temperature so the person belongs in the space.

Avoid: identity drift, copying people from the location reference, changing the location layout, adding extra people, warped hands, warped furniture, broken mirror reflections, visible text, watermarks, artificial compositing edges.
```

## First Wide Anchor For Reels

```text
Generate the first short video or still as a wide creator-space anchor before making close-ups.

Format: [DURATION] / [ASPECT RATIO] / [SINGLE SHOT OR SIMPLE MULTI-SHOT] / realistic social creator footage.

References:
- @person_reference controls identity only.
- @location_reference controls the location, geography, lighting, and atmosphere.
- @spatial_map_reference controls blocking only, if attached.
- @wardrobe_reference controls clothing only, if attached.
- @video_style_reference controls camera, lighting, framing, movement, aspect ratio, and shot quality only, if attached.

Shot: Wide or medium-wide view of the space. Clearly show the room geography, furniture, mirrors, equipment, counters, doors, windows, and where the person is positioned. The person performs one simple everyday action: [SIMPLE ACTION].

Camera: [PHONE SELFIE / TRIPOD / HANDHELD VLOG / MIRROR SHOT / STATIC COUNTERTOP / GYM SIDE ANGLE]. If @video_style_reference is attached, follow its camera, lighting, aspect ratio, shot quality, and movement rules. Keep the space readable. Do not start with an extreme close-up unless a wide anchor already exists.

Performance: Natural influencer behavior. Small pauses, relaxed movement, no overacting. Keep the action simple enough to finish cleanly.

After generation: Save a clean screenshot from this wide shot as @wide_anchor_reference. Use that anchor for later medium shots, close-ups, product shots, and cutaways in the same location.

Avoid: unclear room geography, new furniture, changing the room, extra people, over-cinematic camera moves, dramatic lighting, fake text, watermarks, mismatched lighting.
```

## Close-Up From Wide Anchor

```text
Create a closer creator shot of the person from @person_reference using @wide_anchor_reference as the location truth.

Identity: Preserve the person from @person_reference.

Location continuity: Preserve furniture positions, object placement, decor, equipment, mirror placement, lighting, background geography, and spatial relationships from @wide_anchor_reference. This closer shot must feel like it happens in the same home, gym, office, studio, or daily-life space.

Camera: [CHEST-UP TALKING HEAD / HAND DETAIL / PRODUCT CLOSE-UP / MIRROR CLOSE-UP / OVER-SHOULDER / COUNTERTOP CLOSE-UP / GYM FORM CHECK].

Action: [DESCRIBE THE SMALLER ACTION OR REACTION].

Performance: Natural social content. Use relaxed pauses, glances, small hand movements, and believable timing.

Avoid: resetting the room, cleaning up or moving decor, changing light direction, inventing new background objects, changing identity, extra people, visible text, watermarks.
```

## Lifestyle Still In A Location

```text
Create a realistic AI influencer lifestyle still of the person from @person_reference in the creator location from @location_reference.

Subject: Same person as @person_reference, with preserved identity, age, body type, hair, skin texture, and natural expression.

Setting: Same home, gym, office, studio, or daily-life location as @location_reference. Preserve layout, furniture, equipment, mirrors, materials, lighting, and mood. Keep the setting lived-in and believable.

Wardrobe and props: [DESCRIBE WARDROBE AND ANY PROPS]. Use separate references only for their assigned roles.

Mood: [DESCRIBE SOCIAL POST TONE: calm morning, productive workday, gym reset, cozy evening, polished GRWM, wellness routine, casual errands, quiet luxury, relatable home life].

Composition: [DESCRIBE FRAMING]. Use a social-media-native frame when relevant: 9:16 vertical, 4:5 feed image, 1:1 crop, mirror selfie, phone tripod angle, or candid handheld vlog feel.

Avoid: glossy stock-photo stiffness, changing the person's face, changing the room, floating feet, missing shadows, broken mirror logic, extra people, visible text, watermarks.
```

## Influencer Location Stress Test

```text
Stress-test this creator location before using it as a recurring environment.

Use @location_reference and @person_reference to generate 5-6 short trial stills or video shots:

1. Wide establishing shot with the person standing naturally.
2. Medium shot with the person walking, turning, entering, or crossing the space.
3. Seated, leaning, mirror, counter, desk, bed, or gym-equipment interaction.
4. Close-up with background geography still readable.
5. Object interaction: person picks up, opens, carries, wears, applies, drinks, packs, or sets down a daily object.
6. Alternate time-of-day lighting version, if the influencer will use this location repeatedly.

Judge the location by whether the person moves realistically, hands and feet make physical sense, scale stays stable, mirrors behave, furniture does not warp, equipment stays usable, and the background remains consistent.

If the location produces awkward movement or distorted acting, choose or generate a simpler creator space before building the content series.
```
