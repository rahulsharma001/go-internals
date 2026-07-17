> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[CQRS]].

---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: System Design Patterns (2026-07-05, 6a4aa703-f2d8-83ee-aac3-020aa67e9afb)"
---

# CQRS

## Problem it solves

One model cannot efficiently enforce complex writes and serve very different, high-volume reads.

## Mental model

Write the truth through a guarded front door; build one or more read-friendly views behind it.

## How it works

Commands validate invariants and update the authoritative write model. Committed events update denormalized projections. Queries read projections without changing state. CQRS can be logical—separate models in one database—or physical—different datastores and pipelines.

## Concrete example and detailed dry run

`ConfirmOrder(o-42)` validates payment and inventory, changes the write row to `CONFIRMED`, and emits `OrderConfirmed v2`. A projector consumes it and upserts a customer-order view. The API may return the confirmed command result before the projection catches up; the client sees the new view after bounded lag.

## Success scenario

Writes preserve invariants while each read model is independently optimized and rebuilt from a known event/checkpoint position.

## Failure scenario

The projector crashes after applying an event but before committing its offset. On replay, an idempotent upsert/checkpoint prevents corruption. If a projection bug is discovered, create a corrected version and replay rather than editing history invisibly.

## Scaling considerations

Partition by aggregate, run independent projection consumer groups, monitor projection lag, and plan rebuild capacity. Hot read views can cache aggressively because the authoritative write model remains separate.

## Production technology choices

PostgreSQL for commands, Kafka for change events, Elasticsearch/OpenSearch for search, Redis for hot lookup, and object storage for replayable archives are possible—not mandatory—choices.

## Trade-offs

CQRS gives workload isolation and purpose-built reads, but adds eventual consistency, more schemas, replay/backfill work, and harder debugging.

## When not to use it

Do not use it for ordinary CRUD where one normalized model meets latency and scale needs, or where users require immediate read-after-write from every view.

## Common interview mistakes

- Equating CQRS with event sourcing.
- Ignoring stale reads and user experience.
- Creating many databases before demonstrating a workload need.
- Omitting rebuild and schema-version plans.

## Interview questions and follow-ups

- How will clients handle projection lag?
- How do you rebuild a projection safely?
- What remains the source of truth?

## Five-minute recall

Command model owns invariants; events feed query projections; expect lag; make projectors replayable and idempotent; justify the added complexity.

## Related notes

[[Change Data Capture]] · [[Transactional Outbox Pattern]] · [[Consistency Models]] · [[Caching Pattern]]

## Source metadata

Primary extracted source: *System Design Patterns*, 2026-07-05, conversation ID above.

