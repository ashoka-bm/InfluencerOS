---
status: accepted
---

# Campaign Model Cleanly Replaces Idea Records

Wildcard research without a Campaign owner remains a Content Opportunity in a creator-scoped queue; assigning it creates a Campaign Concept with provenance back to the Opportunity, while campaign-scoped research may create a draft Concept directly. The initial implementation cleanly replaces Idea Queue Entry with Content Opportunity and Idea Promotion with Concept Approval through explicit migration, with no permanent dual-write or schema aliases.

The existing `content_strategy.content_campaigns` records describe recurring anchor-and-derivative publishing patterns rather than the new operational Campaign boundary. They become Content Series, and calendar slots may reference both a Content Series and an operational Campaign. Migration never invents Campaign ownership for promoted legacy work: fixtures may be rebuilt, while durable creator records require explicit Campaign mapping.
