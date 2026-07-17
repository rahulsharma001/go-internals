---
type: quick-revision
domain: system-design
review_time: 4-minutes
---
# HLD Drawing Checklist

## Version 1 first

`client → edge → owning service → source of truth`

Trace one success before adding scale components.

## Label every important element

- meaningful service/store/topic name
- source of truth versus cache/index/replica
- synchronous solid arrow versus asynchronous dashed arrow
- HTTP/gRPC/WebSocket/event where useful
- queue/topic partition key and consumer owner
- cache key/value/TTL and miss path
- commit point and external dependency

## Evolve causally

1. Name measured or reasoned bottleneck.
2. Add one component.
3. Explain routing/ownership.
4. Re-trace the affected flow.
5. State the new failure mode and cost.

Keep the final HLD on one whiteboard; details belong beside the critical path. See [[Building the HLD Incrementally]].
