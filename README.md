# InfluencerOS

InfluencerOS creates universal short-form video ideas and base generation plans for avatar-led social media creators.

The v1 flow:

```text
Choose Creator
  -> research popular short-form social video ideas
  -> use a minimal visual social post format shortlist
  -> produce five creator-fit visual social ideas
  -> choose one idea
  -> apply a format-compatible social template
  -> create a format-specific production plan
  -> create a base generation plan when needed
```

InfluencerOS v1 is platform-agnostic. It targets short vertical videos that can work across Instagram Reels, TikTok, and YouTube Shorts without a platform adapter.

## What V1 Includes

- Creator Profile schema
- Social Research Pack schema
- Social Post Format schema
- five-idea Content Idea Set schema
- Selected Content Idea schema
- Social Template and Applied Social Template schemas
- Micro-Journey Video Plan schema
- Carousel Plan schema
- Single Image Post Plan schema
- Story Sequence Plan schema
- Base Video Generation Plan schema
- conductor skill for the first slice

## What V1 Defers

- platform-specific motion graphics
- caption styling and post-production treatments
- publishing, scheduling, or uploads
- analytics feedback loops
- provider-backed generation without explicit approval

## Validate Examples

```bash
python3 -m unittest discover -s tests
```
