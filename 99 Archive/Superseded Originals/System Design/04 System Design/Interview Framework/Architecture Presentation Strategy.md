> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Building the HLD Incrementally]].

---
type: canonical
domain: system-design
topic: architecture-presentation
status: learning
---
# Architecture Presentation Strategy

## Problem it solves

A correct design can still fail an interview when the diagram is unreadable, choices appear unmotivated, or the candidate never proves the flow.

## Mental model and method

Present in layers: edge, stateless compute, state owners, asynchronous boundary, workers/downstreams. Draw the smallest design that serves the critical flow. Label sync/async arrows, partition keys, source of truth, caches, and failure boundaries. Then walk one success path and one failure path using numbered steps.

## Concrete example and dry run

```text
Client -> Gateway -> Order Service -> PostgreSQL
                           | same transaction
                           +-> outbox -> Debezium -> Kafka -> consumers
```

Say: “PostgreSQL is the order source of truth. The response confirms durable acceptance, not completed payment. Debezium relays committed outbox inserts; Kafka buffers independent consumers.” Then choose payment failure and trace compensation. This narrative makes every box earn its place.

## Success and failure scenarios

Success: the interviewer can point to state ownership, completion semantics, and the first bottleneck. Failure: a cloud-logo diagram with no data flow, or endless box additions. Recover by returning to the critical request and deleting optional components.

## Scaling and production choices

Discuss one deep bottleneck at a time: partition key/hotspot, cache behavior, DB connections, consumer lag, long-lived sockets, or provider quotas. Name concrete technologies as swappable examples and state required semantics first.

## Trade-offs and when not to use

More layers improve isolation but add latency and operations. Async work improves resilience/throughput but complicates consistency and debugging. Do not draw multi-region, service mesh, Kafka, and Redis for a workload that fits a single transactional service.

## Interview mistakes and follow-ups

Unlabeled arrows, queues without delivery semantics, caches without invalidation, replicas treated as zero-lag, and no failure boundary. Follow-ups: what happens after timeout? where is backpressure? what is authoritative? how does a deploy migrate schemas?

## Five-minute recall

Smallest diagram → label state/arrow semantics → success walk → failure walk → first bottleneck → one alternative/trade-off.

Related: [[System Design Interview Framework]], [[Trade-off Communication]], [[Failure Handling Strategy]].

## Source metadata

Based on existing framework, `System Design Practice Tips` (`681749e6…`), and curated event-pipeline examples.
