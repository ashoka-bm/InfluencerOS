---
name: promote-idea
description: Deprecated compatibility route. Halts and redirects old Idea Promotion requests to approve-concept.
---

# Deprecated: Promote Idea

Halt without creating a promotion or Project. Idea Promotion has been replaced
by Campaign Concept assignment plus the Concept Approval gate.

Tell the user this runtime skill is stale, then invoke `approve-concept`. Never
create legacy `research/idea-promotions/` records.
