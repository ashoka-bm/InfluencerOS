# Pipeline Contract

InfluencerOS v1 is a typed planning pipeline.

## Pipeline

```text
creator.profile
  -> social.research_pack
  -> social.post_format_shortlist
  -> content.idea_set
  -> content.selected_idea
  -> format-specific template application
  -> format-specific production plan
  -> output.record, when generation or import creates an artifact
```

## Record Types

| Record type | Schema | Example |
| --- | --- | --- |
| Creator Profile | `schemas/creator-profile.schema.json` | `examples/creator-profile.example.json` |
| Social Research Pack | `schemas/social-research-pack.schema.json` | `examples/social-research-pack.example.json` |
| Social Post Format | `schemas/social-post-format.schema.json` | `examples/social-post-format.example.json` |
| Content Idea Set | `schemas/content-idea-set.schema.json` | `examples/content-idea-set.example.json` |
| Selected Content Idea | `schemas/selected-content-idea.schema.json` | `examples/selected-content-idea.example.json` |
| Social Template | `schemas/social-template.schema.json` | `examples/social-template.example.json` |
| Applied Social Template | `schemas/applied-social-template.schema.json` | `examples/applied-social-template.example.json` |
| Micro-Journey Video Plan | `schemas/micro-journey-video-plan.schema.json` | `examples/micro-journey-video-plan.example.json` |
| Carousel Plan | `schemas/carousel-plan.schema.json` | `examples/carousel-plan.example.json` |
| Single Image Post Plan | `schemas/single-image-post-plan.schema.json` | `examples/single-image-post-plan.example.json` |
| Story Sequence Plan | `schemas/story-sequence-plan.schema.json` | `examples/story-sequence-plan.example.json` |
| Base Video Generation Plan | `schemas/base-video-generation-plan.schema.json` | `examples/base-video-generation-plan.example.json` |

## Format-Specific Production Plans

After `AppliedSocialTemplate`, route by `target_format_id`:

- `format_short_form_video` -> `MicroJourneyVideoPlan`, then `BaseVideoGenerationPlan`.
- `format_carousel` -> `CarouselPlan`.
- `format_single_image_post` -> `SingleImagePostPlan`.
- `format_story_sequence` -> `StorySequencePlan`.

## Gate Rules

The user must explicitly choose the Selected Content Idea. The agent may recommend an idea, but it must not record selection on the user's behalf.

The agent may recommend a social template for the chosen idea. If the user does not care which template is used, the agent may apply its recommended template and record the rationale. If multiple reasonable structures would change the post meaning, format, or production burden, ask before locking the Applied Social Template.

Provider-backed generation requires explicit approval for the exact call or batch.

## V1 Research Rule

Social trends change quickly. Each Social Research Pack must record:

- research date,
- research scope,
- sources,
- observed patterns,
- trend confidence,
- fit notes for the Creator Profile.
