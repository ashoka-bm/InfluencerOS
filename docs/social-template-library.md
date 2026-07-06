# Social Template Library

InfluencerOS uses templates after an idea is selected. The idea says what the post is about. The template says how the viewer moves through it.

## Content Beat Spine

Every template is a named arrangement of the Content Beat Spine (ADR 0024): `HOOK → RETAIN → PAYOFF → CTA`, with `packaging` as the pre-hook stage and emotion as a per-beat attribute, never a stage. Each `beat_sequence` item carries a `beat_role` from the closed enum `[hook, retain, payoff, cta, packaging]`; template beats keep their own human labels (`agitate`, `bridge`, `verdict`) while the role gives planning and the learning loop one shared vocabulary. Every template must land at least a `hook` and a `payoff` — validation enforces this. Hook-role beats may carry an optional typed `hook_category`.

## Named Framework Presets

Seeded spine presets live as validating records under `docs/templates/social-templates/`:

- `template_pas` (Problem-Agitate-Solve): problem [hook] -> agitate [retain] -> solve [payoff] -> next step [cta].
- `template_before_after_bridge` (Before-After-Bridge): before [hook] -> after [retain] -> bridge [payoff] -> invite [cta].
- `template_listicle` (Listicle): count promise [hook] -> items [retain] -> best item [payoff] -> keep it [cta].
- `template_myth_truth` (Myth to Truth): myth [hook] -> stakes [retain] -> truth [payoff] -> takeaway [cta].
- `template_i_tried_x` (I Tried X): experiment [hook] -> experience [retain] -> verdict [payoff] -> your turn [cta].

## Starter Set

Structure sketches typed with spine roles; instantiate as full `social-template` records when first used.

### Short-Form Video

- `template_hook_problem_solution`: hook [hook] -> problem [retain] -> solution [retain] -> payoff [payoff].
- `template_constraint_countdown_result`: constraint [hook] -> timer/countdown [retain] -> action [retain] -> result [payoff].
- `template_before_process_payoff`: before state [hook] -> process [retain] -> visible payoff [payoff].

### Carousel

- `template_hook_steps_payoff`: cover hook [hook] -> step sequence [retain] -> payoff/save cue [payoff, cta].
- `template_myth_truth_slides`: myth [hook] -> correction [retain] -> proof/example [retain] -> takeaway [payoff].
- `template_before_after_breakdown`: before [hook] -> after [retain] -> what changed [retain] -> how to try it [payoff].

### Single Image Post

- `template_identity_signal`: one visual signal that reinforces who the creator is (packaging-forward: the image is hook [hook] and payoff [payoff] at once).
- `template_quote_visual`: concise statement [hook] with strong visual styling that lands its own point [payoff].
- `template_avatar_moment`: avatar in a memorable situation [hook] that communicates the niche [payoff].

### Story Sequence

- `template_day_fragment_sequence`: opening fragment [hook] -> day/routine fragments [retain] -> closing moment [payoff].
- `template_bts_mini_arc`: behind-the-scenes setup [hook] -> moment [retain] -> small reveal [payoff].
- `template_teaser_reveal`: tease [hook] -> partial context [retain] -> reveal [payoff].

## Rule

Templates must be compatible with the recommended format. Do not apply a video-only motion structure to a carousel unless each movement can become a slide-level visual beat.
