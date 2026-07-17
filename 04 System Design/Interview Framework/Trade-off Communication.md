---
type: canonical
domain: system-design
topic: tradeoff-communication
status: active
---
# Trade-off Communication

## Strong answer shape

“Requirement **Y** needs semantic **Z**, so I select **X** over **A**. X improves **benefit** but costs **C**. I contain C with **M**, observe **N**, and would switch to A when **W** changes.”

A trade-off needs a selected option. Generic lists of pros/cons avoid the decision.

## Decision dimensions

- correctness vs availability during partition;
- latency vs freshness;
- throughput vs per-item latency;
- synchronous simplicity vs temporal coupling;
- asynchronous resilience vs lag/duplicates;
- precompute/write amplification vs read latency;
- single-writer simplicity vs global write locality;
- normalized flexibility vs denormalized reads;
- isolation vs capacity utilization;
- durability/retention vs cost/privacy;
- managed service velocity vs portability/control.

## Examples

**Feed:** “I choose hybrid fan-out: precompute ordinary users for low read latency, but pull celebrity posts at read time to avoid massive write amplification. The cost is merge complexity and bounded staleness; I track fan-out lag and read-merge latency. Pure write fan-out wins if follower counts are bounded.”

**Payments:** “I keep single-home writes per payment intent because deduplication and ordered transitions matter more than write locality. The cost is cross-region latency and regional failover complexity; I use regional routing, replicated reads, explicit epochs, and reconciliation. Active-active wins only with a proven conflict-free ownership model.”

## Diagram integration

Annotate the affected arrow/store with the decision and consistency. Keep a small rejected-alternatives table. When constraints change, point to the exact branch that changes.

## Weak language to replace

- “Redis is fast” → “A bounded cache reduces repeated reads; source-of-truth fallback and TTL bound staleness.”
- “Kafka is scalable” → “A partitioned durable log gives per-key ordering and replay; it adds lag, duplicates, and broker operations.”
- “NoSQL for scale” → state access path, partition key, consistency, and transaction loss.
- “Exactly once” → name the broker boundary and application idempotency.

## Five-minute revision

Decision → requirement/semantic → alternative → benefit → cost → containment → signal → switch condition.

Related: [[Trade-off Vocabulary]] · [[CAP and PACELC]] · [[Choosing Databases and Storage]].

