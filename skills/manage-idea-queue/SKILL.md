---
name: manage-idea-queue
description: Deprecated compatibility route. Halts and redirects old Idea Queue requests to manage-opportunity-queue.
---

# Deprecated: Manage Idea Queue

Halt without reading or writing creator records. The Idea Queue model has been
replaced by the Content Opportunity Queue.

Tell the user this runtime skill is stale, then invoke
`manage-opportunity-queue`. Never create legacy `research/idea-queue/` records.
